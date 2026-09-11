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
        ["test topic", "--model", "openai/custom-model", "--output-dir", str(tmp_path)],
    )

    assert result.exit_code == 0, result.output
    summarisation_config = get_all_papers_mock.call_args.kwargs["litellm_config"]
    writing_config = write_literature_survey_mock.call_args.kwargs["litellm_config"]
    assert summarisation_config.model == "openai/custom-model"
    assert writing_config.model == "openai/custom-model"


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
