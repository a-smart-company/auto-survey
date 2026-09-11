"""Getting completions from a large language model."""

import logging
import typing as t

import litellm
from litellm.exceptions import (
    APIConnectionError,
    BadRequestError,
    InternalServerError,
    Timeout,
)
from litellm.types.utils import ModelResponse
from pydantic import BaseModel

from auto_survey.data_models import LiteLLMConfig

logger = logging.getLogger("auto_survey")


def get_llm_completion(
    messages: list[dict[str, str]],
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
        BadRequestError:
            If the API server rejects the request for a reason other than an unsupported
            output token limit.
        InternalServerError:
            If the API server returns an error after all retry attempts.
        Timeout:
            If the API request times out after all retry attempts.
    """
    try:
        response = litellm.completion(
            messages=messages,
            temperature=(
                litellm_config.temperature
                if litellm_config.temperature_supported
                else None
            ),
            max_tokens=(max_tokens if litellm_config.max_tokens_supported else None),
            response_format=response_format,
            timeout=litellm_config.timeout_seconds,
            num_retries=litellm_config.num_retries,
            retry_strategy="exponential_backoff_retry",
            **{
                k: v
                for k, v in litellm_config.model_dump().items()
                if k not in ["temperature", "num_retries", "timeout_seconds"]
            },
        )
        assert isinstance(response, ModelResponse)
        choice = response.choices[0]
        assert isinstance(choice, litellm.Choices)
        completion = choice.message.content or ""
        return completion
    except BadRequestError as e:
        disabled_parameters = _disable_unsupported_parameters(
            error=e, litellm_config=litellm_config
        )
        if not disabled_parameters:
            raise
        parameters = ", ".join(disabled_parameters)
        pronoun = "it" if len(disabled_parameters) == 1 else "them"
        logger.warning(
            f"The model endpoint rejected {parameters}; retrying without {pronoun}."
        )
        return get_llm_completion(
            messages=messages,
            max_tokens=max_tokens,
            response_format=response_format,
            litellm_config=litellm_config,
        )
    except (APIConnectionError, InternalServerError, Timeout) as e:
        logger.error(
            f"LLM API call failed after {litellm_config.num_retries + 1} total "
            f"attempts: {e}"
        )
        raise


def _disable_unsupported_parameters(
    error: BadRequestError, litellm_config: LiteLLMConfig
) -> list[str]:
    """Disable optional parameters that an API error explicitly rejects."""
    message = str(error).lower()
    if not (
        "does not support parameters" in message or "unsupported parameter" in message
    ):
        return []

    disabled_parameters: list[str] = []
    if litellm_config.max_tokens_supported and any(
        parameter in message for parameter in ["max_tokens", "max_completion_tokens"]
    ):
        litellm_config.max_tokens_supported = False
        disabled_parameters.append("output token limits")
    if litellm_config.temperature_supported and "temperature" in message:
        litellm_config.temperature_supported = False
        disabled_parameters.append("temperature")
    return disabled_parameters
