# Auto Survey

Auto Survey is a Python CLI that generates literature surveys from a topic. It searches
Semantic Scholar, uses LiteLLM-backed models to select and summarise papers, writes a
Markdown report, and converts the report to PDF.

## Stack

- Python `>=3.11,<4.0` by package metadata; development and CI target 3.11.
- `uv` for Python installation, dependency locking, virtual environments, running tools,
  building, and publishing.
- Click for the CLI, LiteLLM for model providers, HTTPX for Semantic Scholar,
  Docling for extraction, and external Pandoc/WeasyPrint tools for PDF output.
- Hatchling for packaging; pytest, Ruff, mypy, markdownlint, and pre-commit for quality
  checks.

## Layout

| Path | Purpose |
| --- | --- |
| `src/auto_survey/cli.py` | Click entry point and end-to-end pipeline orchestration. |
| `src/auto_survey/search.py` | Search and relevance filtering. |
| `src/auto_survey/summarisation.py` | PDF extraction and paper summaries. |
| `src/auto_survey/writing.py` | Survey and reference generation. |
| `src/auto_survey/llm.py` | Retried, provider-compatible LiteLLM calls. |
| `src/auto_survey/data_models.py` | Pydantic models and LLM response schemas. |
| `src/auto_survey/pdf_conversion.py` | Pandoc/WeasyPrint report conversion. |
| `src/scripts/` | Environment setup and maintainer-only versioning scripts. |
| `tests/` | CLI, LLM wrapper, PDF conversion, and writing tests. |
| `examples/` | Tracked example survey PDFs; not test fixtures. |

The runtime flow is `cli` -> `search` -> `summarisation` -> `writing` ->
`pdf_conversion`. Preserve this separation when adding pipeline behavior.

## Setup and running

Install `uv`, Python dependencies, and the system PDF tools. On macOS:

```bash
brew install pandoc weasyprint
uv python install 3.11
uv sync --all-extras --all-groups --python 3.11
uv run pre-commit install
```

On Ubuntu, install the PDF tools with `sudo apt install pandoc weasyprint`.

`make install` performs a full interactive setup, but it has broader side effects: it
may install or update `uv`, creates `.env`, configures this checkout's Git identity from
`GIT_NAME` and `GIT_EMAIL`, installs hooks, and runs `pre-commit autoupdate`. Prefer the
explicit commands above in an existing checkout unless those side effects are intended.

For local source changes, run:

```bash
uv run auto-survey "<topic>"
uv run auto-survey --help
```

The default provider needs `OPENAI_API_KEY`. Add `SEMANTIC_SCHOLAR_API_KEY` to avoid the
lower unauthenticated API limits. Keep credentials in the ignored `.env`; see the README
for custom providers and `--api-key-env-var`.

## Testing and checks

Run the full local gate before committing:

```bash
make check
make test
```

- `make check` runs every pre-commit hook over the repository. Hooks can rewrite files;
  rerun the command after inspecting fixes.
- `make test` runs pytest and then `readme-cov`. Pytest includes doctests, source
  coverage, strict xfails, warnings-as-errors, and the ten slowest tests.
- `readme-cov` can update the coverage badge in `README.md`; inspect the worktree after
  tests.
- `tests/test_pdf_conversion.py` invokes real Pandoc and WeasyPrint. A machine without
  the executables cannot pass the full suite.

Use focused tests during development, for example:

```bash
uv run pytest tests/test_llm.py
uv run pytest tests/test_cli.py -x
```

Tests mock LLM and pipeline calls; they do not prove that a real provider,
Semantic Scholar, or a complete paid survey run works. Do not use live API calls as
routine tests.

## Conventions

- Keep Python at 88 columns, use double quotes, add type annotations, and write
  Google-style docstrings. Ruff enforces imports, docstrings, annotations, pycodestyle,
  and Pyflakes rules.
- Keep Markdown prose at 88 columns. Run `make check` rather than invoking only Ruff;
  pre-commit also runs mypy, markdownlint, notebook stripping, and file hygiene checks.
- Manage dependencies with `uv add`, `uv remove`, and `uv lock`. Commit `uv.lock` when
  dependency resolution changes; do not hand-edit it.
- Add focused regression tests for behavior changes. Keep provider and network calls
  mocked unless a test is explicitly an integration test.
- Use the repository's established Conventional Commit prefixes such as `feat:`, `fix:`,
  `docs:`, `tests:`, and `chore:`. The emoji advice in `CONTRIBUTING.md` is not enforced
  and does not match recent history.
- Add user-visible changes to the `[Unreleased]` section of `CHANGELOG.md`.
  Documentation-only maintenance does not require an entry.

## Gotchas

- Importing `auto_survey` loads `.env`. Never commit, log, or paste `.env`; it can
  contain Git identity, model-provider credentials, Semantic Scholar credentials, and a
  PyPI token.
- Generated surveys default to `auto_survey_reports/`, which is ignored. Build artifacts
  in `build/` and `dist/` are ignored too. The PDFs in `examples/` are deliberately
  tracked, so update them only when that is part of the task.
- Pydantic and tqdm are currently available transitively but are imported directly. If
  dependency work touches them, declare them explicitly rather than relying on another
  package to install them.
- `make docker` references a root `Dockerfile`, but none is currently tracked. Do not
  treat that target as functional unless a Dockerfile is added.
- As configured in September 2026, pull-request CI checks out `main` explicitly instead
  of the pull-request revision. Run local checks on the actual change; a green PR run is
  not sufficient evidence until the workflow is fixed.
- Release targets are maintainer-only and irreversible. `make bump-*` edits versions and
  the changelog, commits, tags, and pushes. `make publish-*` then uploads to PyPI using
  `PYPI_API_TOKEN` and creates another `.dev` commit. The tag is pushed before upload,
  and subprocess failures are not checked reliably. Never run a bump or publish target
  without explicit release authorization, a clean synchronized `main`, completed local
  checks, and verified credentials.
