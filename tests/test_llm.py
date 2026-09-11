"""Tests for the `llm` module."""

from unittest.mock import Mock

import litellm
import pytest
from litellm.exceptions import BadRequestError
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
        temperature=1.0,
        max_tokens=100,
        response_format=None,
        timeout=30,
        num_retries=3,
        retry_strategy="exponential_backoff_retry",
        model="openai/custom-model",
        api_base="https://example.com/v1",
        api_key="secret",
    )


def test_get_llm_completion_retries_without_unsupported_parameters(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Test retrying and remembering parameters rejected by an endpoint."""
    response = ModelResponse(
        choices=[{"message": {"content": "A completion", "role": "assistant"}}]
    )
    completion_mock = Mock(
        side_effect=[
            BadRequestError(
                message="Model does not support parameters: ['max_completion_tokens']",
                model="gpt-5.6-sol",
                llm_provider="openai",
            ),
            BadRequestError(
                message="Model does not support parameters: ['temperature']",
                model="gpt-5.6-sol",
                llm_provider="openai",
            ),
            response,
            response,
        ]
    )
    monkeypatch.setattr(litellm, "completion", completion_mock)
    config = LiteLLMConfig(
        model="openai/gpt-5.6-sol",
        api_base="http://127.0.0.1:18080/v1",
        api_key="dummy",
    )

    first_completion = get_llm_completion(
        messages=[{"role": "user", "content": "Hello"}],
        max_tokens=100,
        response_format=None,
        litellm_config=config,
    )
    second_completion = get_llm_completion(
        messages=[{"role": "user", "content": "Hello again"}],
        max_tokens=100,
        response_format=None,
        litellm_config=config,
    )

    assert first_completion == "A completion"
    assert second_completion == "A completion"
    assert config.max_tokens_supported is False
    assert config.temperature_supported is False
    assert completion_mock.call_args_list[0].kwargs["max_tokens"] == 100
    assert completion_mock.call_args_list[0].kwargs["temperature"] == 1.0
    assert completion_mock.call_args_list[1].kwargs["max_tokens"] is None
    assert completion_mock.call_args_list[1].kwargs["temperature"] == 1.0
    assert completion_mock.call_args_list[2].kwargs["max_tokens"] is None
    assert completion_mock.call_args_list[2].kwargs["temperature"] is None
    assert completion_mock.call_args_list[3].kwargs["max_tokens"] is None
    assert completion_mock.call_args_list[3].kwargs["temperature"] is None
