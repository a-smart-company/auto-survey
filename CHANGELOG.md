# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](http://keepachangelog.com/en/1.0.0/) and this
project adheres to [Semantic Versioning](http://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added

- Restored `--model` as a shortcut for setting both the summarisation and writing models.
  It cannot be combined with either role-specific model option.

### Fixed

- Corrected the custom inference API instructions and documented how to use
  OpenAI-compatible endpoints with `--api-base`.

## [v0.2.5] - 2026-06-04

### Fixed

- Added retry logic with exponential backoff and timeout handling to LLM API calls to
  handle transient connection errors gracefully. The `LiteLLMConfig` now includes
  `num_retries` (default: 3) and `timeout_seconds` (default: 30) fields to configure
  retry behaviour.

## [v0.2.4] - 2026-04-09

### Changed

- Split up `--model` into `--summarisation-model` and `--writing-model`, as the former
  can be a lightweight model (defaults to `gpt-4.1-mini`) and the latter should ideally
  be a more powerful model (defaults to `gpt-4.1`).

### Fixed

- Improved the identification of references present in the literature survey, which
  previously caused errors where mentioned references were removed from the list of
  references.

## [v0.2.3] - 2026-02-25

### Fixed

- The Semantic Scholar API often returns 500 errors seemingly at random, so if it
  happens, we wait a second and try again. This is now done for all 5xx errors. If we
  fail 10 times in a row, we give up and return an empty list.

## [v0.2.2] - 2026-02-15

### Fixed

- Changed the `--base-url` argument to `--api-base`, as this is what's required by
  LiteLLM.

## [v0.2.1] - 2025-12-01

### Fixed

- Fixed an issue where we would always look for more papers, even when there aren't any
  relevant ones left. This usually happened if the topic was very niche.

## [v0.2.0] - 2025-10-10

### Changed

- We now re-create the References section manually, which ensures consistent formatting,
  correct alphabetical order, and only includes references that were actually cited in
  the literature survey.
- We've added a logo now, and hidden many of the logs. These can be shown with the
  `--verbose` flag.
- We now use the WeasyPrint PDF engine when converting the Markdown literature survey to
  PDF rather than PDFLaTeX, as the latter often had issues with Unicode characters.
- We now check whether `pandoc` and `weasyprint` are installed before attempting to
  convert the generated Markdown survey into PDF, and give an informative error message
  describing how to install these.
- Sometimes the LLMs add a note at the end of the paper. We have now added to the
  writing prompt to refrain from doing this. This might still happen, but the
  probability should be a lot lower now.

### Fixed

- Fixed a bug related to the parsing of the PDFs of some papers, due to the file not
  ending in `.pdf`. This has been fixed now.
- We now catch `docling.ConversionError` during parsing of PDF files, and skip those
  files instead of crashing.
- We now catch all `httpx.RequestError` during fetching of PDF files, and skip those
  files instead of crashing.
- We now catch `CalledProcessError` during conversion to PDF, and give an informative
  error message instead of crashing.
- We now use `docling>=2.55.0` as errors appeared in earlier versions, as they
  refactored their code base.

## [v0.1.2] - 2025-10-09

### Fixed

- The environment variables where not correctly loaded from the `.env` file. This has
  been fixed now.

## [v0.1.1] - 2025-10-09

### Fixed

- Now sets up logging in the `__init__` file. Previously it was set up in the main
  script, which wasn't triggered properly when `auto-survey` was used with `uvx`.

## [v0.1.0] - 2025-10-09

### Added

- First version of the package, which supports conducting literature surveys with the
  `auto-survey` command.
