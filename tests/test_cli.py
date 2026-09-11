"""Tests for the command-line interface."""

from pathlib import Path
from unittest.mock import Mock

import pytest
from click.testing import CliRunner

from auto_survey import cli


def test_model_sets_both_models(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that `--model` sets the summarisation and writing models."""
    get_all_papers_mock = Mock(return_value=[])
    write_literature_survey_mock = Mock(return_value="# Survey")
    monkeypatch.setattr(cli, "get_all_papers", get_all_papers_mock)
    monkeypatch.setattr(cli, "write_literature_survey", write_literature_survey_mock)
    monkeypatch.setattr(cli, "convert_markdown_file_to_pdf", Mock(return_value=True))

    result = CliRunner().invoke(
        cli.main,
        [
            "test topic",
            "--model",
            "openai/custom-model",
            "--temperature",
            "0.7",
            "--output-dir",
            str(tmp_path),
        ],
    )

    assert result.exit_code == 0, result.output
    summarisation_config = get_all_papers_mock.call_args.kwargs["litellm_config"]
    writing_config = write_literature_survey_mock.call_args.kwargs["litellm_config"]
    assert summarisation_config.model == "openai/custom-model"
    assert writing_config.model == "openai/custom-model"
    assert summarisation_config.temperature == 0.7
    assert writing_config.temperature == 0.7


def test_temperature_defaults_to_one(
    monkeypatch: pytest.MonkeyPatch, tmp_path: Path
) -> None:
    """Test that model calls use a temperature of one by default."""
    get_all_papers_mock = Mock(return_value=[])
    monkeypatch.setattr(cli, "get_all_papers", get_all_papers_mock)
    monkeypatch.setattr(cli, "write_literature_survey", Mock(return_value="# Survey"))
    monkeypatch.setattr(cli, "convert_markdown_file_to_pdf", Mock(return_value=True))

    result = CliRunner().invoke(cli.main, ["test topic", "--output-dir", str(tmp_path)])

    assert result.exit_code == 0, result.output
    config = get_all_papers_mock.call_args.kwargs["litellm_config"]
    assert config.temperature == 1.0


def test_temperature_rejects_out_of_range_value() -> None:
    """Test that temperature must be between zero and two."""
    result = CliRunner().invoke(cli.main, ["test topic", "--temperature", "2.1"])

    assert result.exit_code == 2
    assert "2.1 is not in the range 0.0<=x<=2.0" in result.output


@pytest.mark.parametrize(
    argnames="model_options",
    argvalues=[
        ["--model", "shared", "--summarisation-model", "summariser"],
        ["--model", "shared", "--writing-model", "writer"],
        [
            "--model",
            "shared",
            "--summarisation-model",
            "summariser",
            "--writing-model",
            "writer",
        ],
    ],
    ids=["summarisation-conflict", "writing-conflict", "both-conflict"],
)
def test_model_rejects_role_specific_models(model_options: list[str]) -> None:
    """Test that `--model` cannot be combined with role-specific model options."""
    result = CliRunner().invoke(cli.main, ["test topic", *model_options])

    assert result.exit_code == 2
    assert "--model cannot be combined with" in result.output
