"""Read and summarise relevant papers on a given topic."""

import logging
import tempfile
from time import sleep

import httpx
from docling.document_converter import DocumentConverter
from docling.exceptions import ConversionError

from auto_survey.data_models import LiteLLMConfig, Paper, Summary
from auto_survey.llm import get_llm_completion
from auto_survey.utils import no_terminal_output

logger = logging.getLogger("auto_survey")


def summarise_paper(
    paper: Paper, topic: str, verbose: bool, litellm_config: LiteLLMConfig
) -> str:
    """Summarise a paper where the summary focuses on a given topic.

    Args:
        paper:
            The paper to summarise.
        topic:
            The topic to focus the summary on.
        verbose:
            Whether to print verbose output.
        litellm_config:
            The LiteLLM configuration to use.

    Returns:
        The summary of the paper.
    """
    content = ""

    # Try to get the content from the PDF if a URL is provided
    if paper.url != "":
        for _ in range(num_attempts := 3):
            try:
                content = parse_pdf(pdf_url=paper.url, verbose=verbose)
                break
            except httpx.HTTPStatusError as e:
                if e.response.status_code == 403:
                    logger.debug(
                        f"Access forbidden when trying to fetch PDF from {paper.url}."
                    )
                    break
                logger.debug(
                    f"Failed to fetch PDF from {paper.url}. The error was {e!r}. "
                    f"Retrying in a second..."
                )
                sleep(1)
            except httpx.RequestError as e:
                logging.debug(
                    f"Connection error while trying to fetch PDF from {paper.url}. "
                    f"The error was {e!r}. Retrying in a second..."
                )
                sleep(1)
            except ConversionError as e:
                logger.debug(
                    f"Failed to convert PDF from {paper.url} to Markdown. The error "
                    f"was {e!r}."
                )
                break
        else:
            logger.debug(
                f"Failed to fetch PDF from {paper.url}, after {num_attempts} attempts."
            )

    # Truncate the middle of the content if it's too long
    max_content_length = 150_000
    if len(content) > max_content_length:
        half_length = max_content_length // 2
        content = (
            content[:half_length]
            + "\n\n(...content truncated...)\n\n"
            + content[-half_length:]
        )
        logger.debug(
            f"The content from the PDF at {paper.url} was too long, so it was "
            "truncated."
        )

    # If we couldn't get the content from the PDF, use the title and summary
    if content == "":
        content = f"# {paper.title}"
        if paper.summary != "":
            content += f"\n\n## Summary\n\n{paper.summary}"

    system_prompt = """
        You are an expert research assistant. Your task is to read and summarise
        research papers. The summary should focus on the provided topic, highlighting
        the most relevant points from the paper. The summary should be concise and
        informative.
    """.strip()

    user_prompt = f"""
        Summarise the following paper, focusing on the topic {topic!r}. The summary
        should be concise and informative, highlighting the most relevant points from
        the paper.

        <paper>
        {content}
        </paper>

        You should return a JSON dictionary with a single key 'summary' mapping to the
        summary string.
    """.strip()

    completion = get_llm_completion(
        messages=[
            dict(role="system", content=system_prompt),
            dict(role="user", content=user_prompt),
        ],
        max_tokens=1024,
        response_format=Summary,
        litellm_config=litellm_config,
    )
    summary = Summary.model_validate_json(json_data=completion).summary
    return summary


def parse_pdf(pdf_url: str, verbose: bool) -> str:
    """Parse the content of a PDF from a URL and convert it to Markdown.

    Args:
        pdf_url:
            The URL of the PDF to parse.
        verbose:
            Whether to print verbose output.

    Returns:
        The content of the PDF converted to Markdown.

    Raises:
        httpx.HTTPStatusError:
            If the PDF URL returns a non-200 status code.
    """
    # Get the raw PDF. We use a normal-looking header here to prevent blocking
    headers = {
        "User-Agent": (
            "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.15; rv:143.0) Gecko/20100101 "
            "Firefox/143.0"
        )
    }
    response = httpx.get(
        url=pdf_url, headers=headers, follow_redirects=True, timeout=30
    )
    response.raise_for_status()

    # Parse the raw PDF as Markdown
    with (
        tempfile.NamedTemporaryFile(mode="w+b", suffix=".pdf") as temp_file,
        no_terminal_output(disable=verbose),
    ):
        temp_file.write(response.content)
        temp_file.flush()
        result = DocumentConverter().convert(source=temp_file.name)
    markdown = result.document.export_to_markdown()

    return markdown
