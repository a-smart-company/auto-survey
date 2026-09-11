"""Tests for the `llm` module."""

from unittest.mock import Mock

import litellm
import pytest
from litellm.types.utils import ModelResponse

from auto_survey.data_models import LiteLLMConfig
from auto_survey.llm import get_llm_completion


def test_get_llm_completion_forwards_openai_compatible_endpoint(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test forwarding configuration for an OpenAI-compatible endpoint."""
    completion_mock = Mock(
        return_value=ModelResponse(
            choices=[{"message": {"content": "A completion", "role": "assistant"}}]
        )
    )
    monkeypatch.setattr(litellm, "completion", completion_mock)

    completion = get_llm_completion(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.0,
        max_tokens=100,
        response_format=None,
        litellm_config=LiteLLMConfig(
            model="openai/custom-model",
            api_base="https://example.com/v1",
            api_key="secret",
        ),
    )

    assert completion == "A completion"
    completion_mock.assert_called_once_with(
        messages=[{"role": "user", "content": "Hello"}],
        temperature=0.0,
        max_tokens=100,
        response_format=None,
        timeout=30,
        num_retries=3,
        retry_strategy="exponential_backoff_retry",
        model="openai/custom-model",
        api_base="https://example.com/v1",
        api_key="secret",
    )
