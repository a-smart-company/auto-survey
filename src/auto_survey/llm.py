"""Getting completions from a large language model."""

import logging
import typing as t

import litellm
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
    """
    config_dict = litellm_config.model_dump()
    num_retries = config_dict.pop("num_retries", 3)
    timeout = config_dict.pop("timeout_seconds", 30)

    for attempt in range(num_retries):
        try:
            response = litellm.completion(
                messages=messages,
                temperature=temperature,
                max_tokens=max_tokens,
                response_format=response_format,
                timeout=timeout,
                **config_dict,
            )
            break
        except Exception as e:
            if attempt < num_retries - 1:
                logger.warning(
                    f"LLM API call failed (attempt {attempt + 1}/{num_retries}): {e}"
                )
            else:
                logger.error(f"LLM API call failed after {num_retries} attempts: {e}")
                raise
    assert isinstance(response, ModelResponse)
    choice = response.choices[0]
    assert isinstance(choice, litellm.Choices)
    completion = choice.message.content or ""
    return completion
