# When game reviews are funnier than the game - Adding context to identify humor in Steam reviews

> This project was created as part of a seminar paper at the University of Cologne.

In this seminar paper, I investigated whether a BERT model ([bert-base-uncased](https://huggingface.co/google-bert/bert-base-uncased)) can correctly identify humor levels in Steam game user reviews. The goal was to answer the following three research questions:

- RQ 1: Is BERT able to correctly identify humor in reviews without any finetuning?
- RQ 2: Does finetuning improve BERT's ability to correctly identify humor in reviews?
- RQ 3: Does additional context positively influence BERT's ability to identify humor in reviews?

For this, a new dataset was created from Steam user reviews retrieved via the [Steamworks User Reviews - Get List API](https://partner.steamgames.com/doc/store/getreviews?l=english). Reviews were automatically labeled with both a min-max label and a categorical label based on the `votes_funny` field.

Using [MLM](https://huggingface.co/docs/transformers/tasks/masked_language_modeling), we ran multiple experiments with five prompt variations (two prompts guiding the model to predict values between 0.0 and 0.9, and three prompts guiding the model to predict humor-related tokens).

To answer RQ 1 and RQ 2, we first evaluated performance using [bert-base-uncased](https://huggingface.co/google-bert/bert-base-uncased). We then finetuned the model and reported performance metrics again.

To answer RQ 3, we augmented review text with game-related metadata (game name, whether the review recommends the game, game categories, and game genres) and ran the same evaluation and finetuning process again.

This README is primarily for code usage instructions.

## Requirements

- Git
- Python version from [`.python-version`](./.python-version)
- [uv](https://docs.astral.sh/uv/) for environment and dependency management

## Quick Start

### 1. Setup with `uv`

Install `uv`:

**macOS / Linux**

```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

**Windows (PowerShell)**

```powershell
powershell -ExecutionPolicy ByPass -c "irm https://astral.sh/uv/install.ps1 | iex"
```

Clone the repository and sync dependencies:

```bash
git clone https://github.com/tdiepenb/steamReviewHumor.git
cd steamReviewHumor
uv sync
```

`uv sync` creates the local environment and installs dependencies from `uv.lock`.

### 2. Create the dataset

1. Edit [steam_review_humor/config.py](./steam_review_humor/config.py) to adjust:
   - `APP_IDS` (games to include)
   - download settings (for example language, review limits, timeouts)
   - preprocessing and labeling thresholds
2. Download Steam reviews:

```bash
uv run python -m steam_review_humor.main_downloader
```

3. Convert downloaded data into CSV:

```bash
uv run python -m steam_review_humor.main_convert_to_csv
```

### 3. Run experiments and evaluate

- Use [data_exploration.ipynb](./data_exploration.ipynb) to inspect and understand the dataset.
- Use [bert_review_text_only.ipynb](./bert_review_text_only.ipynb) and [bert_review_text_app_info.ipynb](./bert_review_text_app_info.ipynb) to run model evaluation and finetuning.
- Use [evaluation.ipynb](./evaluation.ipynb) to compare model variants and analyze differences.
