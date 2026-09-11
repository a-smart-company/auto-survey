<!-- This disables the requirement that the first line is a top-level heading -->
<!-- markdownlint-configure-file { "MD041": false } -->

<div align='center'>
<img
    src="https://raw.githubusercontent.com/saattrupdan/auto-survey/refs/heads/main/gfx/auto-survey-logo.png"
    height="216"
    width="1154"
>
</div>

### Automated literature surveys

______________________________________________________________________
[![PyPI Status](https://badge.fury.io/py/auto_survey.svg)](https://pypi.org/project/auto_survey/)
[![Code Coverage](https://img.shields.io/badge/Coverage-50%25-orange.svg)](https://github.com/saattrupdan/auto-survey/tree/main/tests)
[![License](https://img.shields.io/github/license/saattrupdan/auto-survey)](https://github.com/saattrupdan/auto-survey/blob/main/LICENSE)
[![LastCommit](https://img.shields.io/github/last-commit/saattrupdan/auto-survey)](https://github.com/saattrupdan/auto-survey/commits/main)
[![Contributor Covenant](https://img.shields.io/badge/Contributor%20Covenant-2.0-4baaaa.svg)](https://github.com/saattrupdan/auto-survey/blob/main/CODE_OF_CONDUCT.md)

Developer:

- Dan Saattrup Smart (<saattrupdan@gmail.com>)

## Getting Started

### Get a Semantic Scholar API key

The first thing to do is to [request an API key for Semantic
Scholar](https://www.semanticscholar.org/product/api#api-key-form). Note that this can
only be used for research purposes. Here are some suggested answers for the form:

```markdown
> How do you plan to use Semantic Scholar API in your project? (50 words or more)*

Generate literature surveys using large language models with relevant papers in context, using the `auto-survey` Python package. It re-writes the desired research topic into 10 different queries, pings the /paper/search endpoint for each of those for papers, and feeds those papers to a language model to generate a literature survey. It is only for my own private use.

> Which endpoints do you plan to use?

The /paper/search endpoint.

> How many requests per day do you anticipate using?

Around 100 requests per day.
```

When you have it, you create a file called `.env` in your current directory with the
following content:

```bash
SEMANTIC_SCHOLAR_API_KEY="<your key here>"
```

If you already had a `.env` file, you can just append the line above to it.

### Set up an LLM API key

Next, you need to set up an API key for the large language model (LLM) that you want to
use. The default model is `gpt-4.1-mini` from OpenAI, which requires you to have an
OpenAI API key, and again add it to your `.env` file:

```bash
OPENAI_API_KEY="<your key here>"
```

### Installing and Running

Firstly, you need to install the `pandoc` and `weasyprint` packages, which allows for
generating the final PDFs. You can do this on MacOS using [Homebrew](https://brew.sh/):

```bash
brew install pandoc weasyprint
```

On Ubuntu you can install them with `apt`:

```bash
sudo apt install pandoc weasyprint
```

Then, the easiest way to use the `auto-survey` package is as a
[uv](https://docs.astral.sh/uv/getting-started/installation/) tool. You can start
generating a literature survey using the following command:

```bash
uvx auto-survey "<your topic here>"
```

This both installs the package and creates the literature survey, which typically takes
about 10 minutes. With the default model, it costs about $0.05 per survey.

You can see all the available options by running the
following command:

```bash
uvx auto-survey --help
```

## Using Different Model Providers

The package supports all of [LiteLLM's
providers](https://docs.litellm.ai/docs/providers/), including OpenAI, Anthropic,
Google, xAI, local models, and more. You can simply set the `--model` argument to the
model you want to use. For example, to use Claude Sonnet 4.5 from Anthropic, use

```bash
uvx auto-survey "<your topic here>" --model "claude-sonnet-4-5"
```

`--model` uses the same model for summarisation and writing. To choose different models,
use `--summarisation-model` and `--writing-model` instead. `--model` cannot be combined
with either role-specific option. The `--temperature` option controls the sampling
temperature for all model calls and defaults to `1.0`.

Some providers require you to prefix the model ID with the provider name. For instance,
to use the Grok-3-mini model from xAI, you need to use

```bash
uvx auto-survey "<your topic here>" --model "xai/grok-3-mini"
```

All of this is documented in the [LiteLLM provider
documentation](https://docs.litellm.ai/docs/providers). If you use a different provider,
you need to set different environment variables. See the [LiteLLM provider
documentation](https://docs.litellm.ai/docs/providers) for more information on which
environment variables to set.

### Custom Inference API

You can use any OpenAI-compatible endpoint by setting `--api-base` to its base URL and
prefixing each model ID with `openai/`:

```bash
uvx auto-survey "<your topic here>" \
  --model "openai/<model-id>" \
  --api-base "http://127.0.0.1:18080/v1"
```

When no API key is provided, Auto Survey sends a non-secret dummy key for compatibility
with OpenAI clients. If a custom endpoint rejects optional parameters such as an output
token limit or temperature, Auto Survey automatically retries without them for that
model. If the endpoint requires authentication, store its API key in `.env` and pass the
environment variable name with `--api-key-env-var`:

```bash
CUSTOM_LLM_API_KEY="<your key here>"

uvx auto-survey "<your topic here>" \
  --model "openai/<model-id>" \
  --api-base "https://example.com/v1" \
  --api-key-env-var "CUSTOM_LLM_API_KEY"
```

Other custom inference servers may require a different LiteLLM provider prefix. For
example, vLLM uses `hosted_vllm/` and Ollama uses `ollama_chat/`. See the [LiteLLM
provider documentation](https://docs.litellm.ai/docs/providers) for the available
prefixes.
