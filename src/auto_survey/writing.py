"""Writing up literature surveys."""

import logging

from auto_survey.data_models import LiteLLMConfig, Paper
from auto_survey.llm import get_llm_completion

logger = logging.getLogger("auto_survey")


def write_literature_survey(
    topic: str, relevant_papers: list[Paper], litellm_config: LiteLLMConfig
) -> str:
    """Write a literature survey on a given topic using relevant papers.

    Args:
        topic:
            The topic to write the literature survey on.
        papers_with_summaries:
            A dictionary mapping relevant papers to their summaries.
        litellm_config:
            The LiteLLM configuration to use.

    Returns:
        The literature survey, as a Markdown string.
    """
    logger.info("Writing literature survey based on the papers...")

    system_prompt = """
        You are an expert academic researcher and writer.

        Your task is to write a literature survey on a given topic using the provided
        relevant papers. The literature survey should be well-structured, comprehensive,
        and written in clear, concise English.

        The literature survey should be formatted in Markdown, with appropriate
        headings, subheadings, and paragraphs. Rather than simply listing each paper
        summary one after the other, you should synthesise the information from the
        papers to provide a coherent overview of the topic.

        The survey should include:
        - An introduction to the topic (named "Introduction"), explaining its
          significance and context.
        - 2-3 main content sections, each with multiple paragraphs separated by double
          newlines, covering different aspects of the topic. Each section should
          synthesise information from multiple papers, highlighting information that is
          relevant to the topic.
        - A conclusion (named "Conclusion") that summarises the key points discussed in
          the survey.
        - A references section (named "## References") that lists all the papers cited
          in the survey, formatted in APA style. This means that the references should
          be of the form "Author (Year)" or "(Author, Year)", depending on the sentence
          structure. If there are 2 authors use "Author1 and Author2 (Year)" or
          "(Author1 and Author2, Year)". If there are 3 or more authors use "Author1 et
          al. (Year)" or "(Author1 et al., Year)". This is IMPORTANT: follow this format
          EXACTLY, AT ALL TIMES.

        Return only the Markdown content of the literature survey, without any
        additional commentary or explanation.
    """.strip()

    # Remove URLs from the papers, to avoid URLs cluttering the references
    logger.debug("Removing URLs from the papers to avoid cluttering the references...")
    for paper in relevant_papers:
        paper.url = ""

    papers_str = "\n\n".join(str(paper) for paper in relevant_papers)
    user_prompt = f"""
        Write a literature survey on the topic of {topic!r}, using the following
        relevant papers:

        <papers>
        {papers_str}
        </papers>
    """.strip()

    literature_survey = get_llm_completion(
        messages=[
            dict(role="system", content=system_prompt),
            dict(role="user", content=user_prompt),
        ],
        max_tokens=10_000,
        litellm_config=litellm_config,
        response_format=None,
    )
    literature_survey = correct_references(
        literature_survey=literature_survey, papers=relevant_papers
    )
    return literature_survey


def correct_references(literature_survey: str, papers: list[Paper]) -> str:
    """Recreate the references section of a literature survey.

    This ensures that all references are formatted correctly and consistently, and that
    any unused references are not included.

    Args:
        literature_survey:
            The literature survey, as a Markdown string.
        papers:
            The list of all papers that were used to write the literature survey.

    Returns:
        The literature survey with any unused references removed, as a Markdown string.
    """
    # Collect a list of all the cited papers
    cited_papers: list[Paper] = list()
    for paper in papers:
        citation_in_parens = paper.get_citation(in_parens=True)
        citation_without_any_parens = citation_in_parens[1:-1]
        citation_with_year_in_parens = paper.get_citation(in_parens=False)
        if citation_without_any_parens.replace(",", "") in literature_survey.replace(
            ",", ""
        ) or citation_with_year_in_parens.replace(",", "") in literature_survey.replace(
            ",", ""
        ):
            cited_papers.append(paper)

    # Remove the existing references section
    literature_survey = literature_survey.rsplit("## References")[0].strip()

    # Create a new references section
    papers_and_entries = [(paper, paper.references_entry()) for paper in cited_papers]
    papers_and_entries = sorted(
        papers_and_entries,
        key=lambda pair: pair[0].authors[0].last_name if pair[0].authors else "",
    )
    references_entries = list(dict(papers_and_entries).values())
    references_section = "## References\n\n" + "\n\n".join(references_entries)

    # Add the new references section to the literature survey
    literature_survey = literature_survey + "\n\n" + references_section

    return literature_survey
