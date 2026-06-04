"""Getting completions from a large language model."""

import logging
import typing as t

import litellm
from litellm.exceptions import APIConnectionError, InternalServerError
from litellm.types.utils import ModelResponse
from pydantic import BaseModel

from auto_survey.data_models import LiteLLMConfig

logger = logging.getLogger("auto_survey")


def get_llm_completion(
    messages: list[dict[str, str]],
    temperature: float,
    max_tokens: int,
    response_format: t.Type[BaseModel] | None,
    litellm_config: LiteLLMConfig,
) -> str:
    """Get a completion from the LLM.

    Args:
        messages:
            The messages to use for the completion. Each message is a dict with keys
            "role" and "content". The "role" can be "system", "user", or "assistant".
            The "content" is the content of the message.
        temperature:
            The temperature to use for the completion.
        max_tokens:
            The maximum number of tokens to generate.
        response_format:
            The response format to use. Can be None if no specific format is needed.
        litellm_config:
            The LiteLLM configuration to use.

    Returns:
        The completion from the LLM.

    Raises:
        APIConnectionError:
            If the API connection fails after all retry attempts.
        InternalServerError:
            If the API server returns an error after all retry attempts.
    """
    try:
        response = litellm.completion(
            messages=messages,
            temperature=temperature,
            max_tokens=max_tokens,
            response_format=response_format,
            timeout=litellm_config.timeout_seconds,
            num_retries=litellm_config.num_retries,
            retry_strategy="exponential_backoff_retry",
            **{
                k: v
                for k, v in litellm_config.model_dump().items()
                if k not in ["num_retries", "timeout_seconds"]
            },
        )
        assert isinstance(response, ModelResponse)
        choice = response.choices[0]
        assert isinstance(choice, litellm.Choices)
        completion = choice.message.content or ""
        return completion
    except (APIConnectionError, InternalServerError) as e:
        logger.error(
            f"LLM API call failed after {litellm_config.num_retries + 1} total "
            f"attempts: {e}"
        )
        raise
