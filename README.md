# EECS 4312 SpecChain Project

## Application Studied
This project analyzes user reviews for the **Headspace** Android app (`com.getsomeheadspace.android`) and turns them into software engineering artifacts across three pipelines: manual, automated, and hybrid.

## Dataset
- `data/reviews_raw.jsonl` contains the collected Google Play reviews.
- `data/reviews_clean.jsonl` contains the cleaned review dataset used by the pipelines.
- Raw dataset size: **5000** reviews.
- Final cleaned dataset size: **4734** reviews.
- Data collection method: **google-play-scraper Python library**.
- Cleaning metadata is stored in `data/dataset_metadata.json`.

## Repository Structure
- `data/` contains the raw and cleaned datasets and the review groups for each pipeline.
- `personas/` contains the manual, automated, and hybrid persona files.
- `spec/` contains the manual, automated, and hybrid specifications.
- `tests/` contains the validation tests for each pipeline.
- `metrics/` contains per-pipeline metrics and the comparison summary.
- `prompts/` contains the prompts used in the automated pipeline.
- `src/` contains the executable Python scripts.
- `reflection/` contains the final project reflection.

## Main Files
- `src/00_validate_repo.py` checks that the required folders and files exist.
- `src/01_collect_or_import.py` recollects raw Google Play reviews.
- `src/02_clean.py` cleans the raw dataset into the committed cleaned dataset format.
- `src/run_all.py` runs the automated pipeline from the raw dataset through automated metrics.
- `src/05_personas_auto.py` generates automated review groups and personas.
- `src/06_spec_generate.py` generates the automated specification.
- `src/07_tests_generate.py` generates the automated validation tests.
- `src/08_metrics.py` computes metrics for one pipeline or for all pipelines together.

## Exact Commands
Validate the repository structure:

```bash
python3 src/00_validate_repo.py
```

Run the automated pipeline from the committed raw dataset:

```bash
export GROQ_API_KEY="your_key_here"
python3 src/run_all.py
```

Recompute metrics for all three pipelines and refresh the comparison summary:

```bash
python3 src/08_metrics.py --pipeline all
```

Run the automated steps one by one:

```bash
python3 src/02_clean.py
python3 src/05_personas_auto.py
python3 src/06_spec_generate.py
python3 src/07_tests_generate.py
python3 src/08_metrics.py --pipeline automated
```

## Notes
- `src/run_all.py` uses the committed `data/reviews_raw.jsonl` file by default.
- `GROQ_API_KEY` must be set before running the automated pipeline scripts.
- To recollect the raw dataset, install `google_play_scraper` and run:

```bash
python3 src/01_collect_or_import.py
```
