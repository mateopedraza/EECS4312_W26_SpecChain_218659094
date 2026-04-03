"""Run the automated pipeline from raw reviews to automated metrics.

Order:
1. Load or collect raw reviews.
2. Clean them into ``data/reviews_clean.jsonl`` and ``data/dataset_metadata.json``.
3. Generate ``data/review_groups_auto.json`` and ``personas/personas_auto.json``.
4. Generate ``spec/spec_auto.md``.
5. Generate ``tests/tests_auto.json``.
6. Generate ``metrics/metrics_auto.json``.

The automated generation steps require ``GROQ_API_KEY``.
"""

from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
RAW_PATH = ROOT / "data" / "reviews_raw.jsonl"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Run the automated pipeline end to end.")
    parser.add_argument(
        "--collect-raw",
        action="store_true",
        help="Refresh data/reviews_raw.jsonl by running src/01_collect_or_import.py first.",
    )
    return parser.parse_args()


def run_step(title: str, command: list[str]) -> None:
    print(f"\n== {title} ==", flush=True)
    print("Running:", " ".join(command), flush=True)
    subprocess.run(command, check=True, cwd=ROOT)


def main() -> int:
    args = parse_args()
    python_cmd = sys.executable
    if not os.getenv("GROQ_API_KEY"):
        raise RuntimeError(
            "GROQ_API_KEY is not set. Export it before running src/run_all.py."
        )

    print("Starting automated pipeline...", flush=True)
    print(f"Repository root: {ROOT}", flush=True)

    if args.collect_raw or not RAW_PATH.exists():
        run_step(
            "Collect Raw Reviews",
            [python_cmd, str(SRC / "01_collect_or_import.py")],
        )
    else:
        print("\n== Collect Raw Reviews ==", flush=True)
        print(f"Using existing raw dataset: {RAW_PATH}", flush=True)

    run_step(
        "Clean Reviews",
        [python_cmd, str(SRC / "02_clean.py")],
    )

    run_step(
        "Generate Automated Review Groups and Personas",
        [python_cmd, str(SRC / "05_personas_auto.py")],
    )

    run_step(
        "Generate Automated Specification",
        [python_cmd, str(SRC / "06_spec_generate.py")],
    )

    run_step(
        "Generate Automated Tests",
        [python_cmd, str(SRC / "07_tests_generate.py")],
    )

    run_step(
        "Compute Automated Metrics",
        [python_cmd, str(SRC / "08_metrics.py"), "--pipeline", "automated"],
    )

    print("\nAutomated pipeline complete.", flush=True)
    print("Produced files:", flush=True)
    print("- data/reviews_clean.jsonl", flush=True)
    print("- data/dataset_metadata.json", flush=True)
    print("- data/review_groups_auto.json", flush=True)
    print("- personas/personas_auto.json", flush=True)
    print("- spec/spec_auto.md", flush=True)
    print("- tests/tests_auto.json", flush=True)
    print("- metrics/metrics_auto.json", flush=True)
    print("- prompts/prompt_auto.json", flush=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
