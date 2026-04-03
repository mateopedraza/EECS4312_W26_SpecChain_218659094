"""Compute metrics for the manual, automated, and hybrid pipelines."""

from __future__ import annotations

import argparse
import re
from pathlib import Path

from auto_pipeline_utils import ROOT, load_json, save_json


DEFAULTS = {
    "manual": {
        "groups": ROOT / "data" / "review_groups_manual.json",
        "personas": ROOT / "personas" / "personas_manual.json",
        "spec": ROOT / "spec" / "spec_manual.md",
        "tests": ROOT / "tests" / "tests_manual.json",
        "metrics": ROOT / "metrics" / "metrics_manual.json",
    },
    "automated": {
        "groups": ROOT / "data" / "review_groups_auto.json",
        "personas": ROOT / "personas" / "personas_auto.json",
        "spec": ROOT / "spec" / "spec_auto.md",
        "tests": ROOT / "tests" / "tests_auto.json",
        "metrics": ROOT / "metrics" / "metrics_auto.json",
    },
    "hybrid": {
        "groups": ROOT / "data" / "review_groups_hybrid.json",
        "personas": ROOT / "personas" / "personas_hybrid.json",
        "spec": ROOT / "spec" / "spec_hybrid.md",
        "tests": ROOT / "tests" / "tests_hybrid.json",
        "metrics": ROOT / "metrics" / "metrics_hybrid.json",
    },
}

DATASET_PATH = ROOT / "data" / "reviews_clean.jsonl"
SUMMARY_PATH = ROOT / "metrics" / "metrics_summary.json"
AMBIGUOUS_TERMS = {
    "fast",
    "quick",
    "quickly",
    "easy",
    "easily",
    "simple",
    "better",
    "best",
    "user friendly",
    "user-friendly",
    "intuitive",
    "seamless",
    "smooth",
    "efficient",
    "convenient",
    "robust",
    "friendly",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Compute pipeline metrics.")
    parser.add_argument(
        "--pipeline",
        choices=sorted(DEFAULTS) + ["all"],
        default="automated",
        help="Which pipeline artifacts to measure. Use 'all' to write every metrics file and the summary file.",
    )
    return parser.parse_args()


def parse_requirements(spec_path: Path) -> list[dict[str, str]]:
    text = spec_path.read_text(encoding="utf-8")
    raw_blocks = re.split(r"(?m)^# Requirement ID: ", text)[1:]
    requirements = []
    for block in raw_blocks:
        lines = block.strip().splitlines()
        requirement_id = lines[0].strip()
        description = ""
        traceability = ""
        for line in lines[1:]:
            if line.startswith("- Description: ["):
                description = line[len("- Description: [") : -1]
            elif line.startswith("- Traceability: ["):
                traceability = line[len("- Traceability: [") : -1]
        requirements.append(
            {
                "requirement_id": requirement_id,
                "description": description,
                "traceability": traceability,
                "raw": block.lower(),
            }
        )
    return requirements


def count_clean_reviews(path: Path) -> int:
    with path.open("r", encoding="utf-8") as handle:
        return sum(1 for _ in handle if _.strip())


def compute_metrics(
    pipeline_name: str,
    groups_path: Path,
    personas_path: Path,
    spec_path: Path,
    tests_path: Path,
) -> dict[str, float | int | str]:
    groups_payload = load_json(groups_path, default={}) or {}
    personas_payload = load_json(personas_path, default={}) or {}
    tests_payload = load_json(tests_path, default={}) or {}

    groups = groups_payload.get("groups", [])
    personas = personas_payload.get("personas", [])
    tests = tests_payload.get("tests", [])
    requirements = parse_requirements(spec_path)

    dataset_size = count_clean_reviews(DATASET_PATH)
    persona_count = len(personas)
    requirements_count = len(requirements)
    tests_count = len(tests)

    derived_groups = {persona.get("derived_from_group") for persona in personas}
    covered_review_ids = set()
    for group in groups:
        if group.get("group_id") in derived_groups:
            covered_review_ids.update(group.get("review_ids", []))

    review_group_links = sum(
        len(group.get("review_ids", []))
        for group in groups
        if group.get("group_id") in derived_groups
    )
    group_persona_links = persona_count
    requirement_persona_links = sum(
        1 for requirement in requirements if "persona" in requirement["traceability"].lower()
    )
    test_requirement_links = sum(
        1 for test in tests if isinstance(test.get("requirement_id"), str)
    )

    traceability_links = (
        review_group_links
        + group_persona_links
        + requirement_persona_links
        + test_requirement_links
    )

    review_coverage = (
        round(len(covered_review_ids) / dataset_size, 4) if dataset_size else 0.0
    )
    traceability_ratio = (
        round(requirement_persona_links / requirements_count, 4)
        if requirements_count
        else 0.0
    )

    requirement_ids = {requirement["requirement_id"] for requirement in requirements}
    tested_requirement_ids = {
        test.get("requirement_id") for test in tests if isinstance(test.get("requirement_id"), str)
    }
    testability_rate = (
        round(len(requirement_ids & tested_requirement_ids) / requirements_count, 4)
        if requirements_count
        else 0.0
    )

    ambiguous_requirements = 0
    for requirement in requirements:
        text = requirement["raw"]
        if any(term in text for term in AMBIGUOUS_TERMS):
            ambiguous_requirements += 1
    ambiguity_ratio = (
        round(ambiguous_requirements / requirements_count, 4)
        if requirements_count
        else 0.0
    )

    return {
        "pipeline": pipeline_name,
        "dataset_size": dataset_size,
        "persona_count": persona_count,
        "requirements_count": requirements_count,
        "tests_count": tests_count,
        "traceability_links": traceability_links,
        "review_coverage": review_coverage,
        "traceability_ratio": traceability_ratio,
        "testability_rate": testability_rate,
        "ambiguity_ratio": ambiguity_ratio,
    }


def compute_pipeline_metrics(pipeline_name: str) -> dict[str, float | int | str]:
    paths = DEFAULTS[pipeline_name]
    return compute_metrics(
        pipeline_name,
        paths["groups"],
        paths["personas"],
        paths["spec"],
        paths["tests"],
    )


def write_all_metrics() -> dict[str, dict[str, float | int | str]]:
    summary: dict[str, dict[str, float | int | str]] = {}
    for pipeline_name, paths in DEFAULTS.items():
        metrics = compute_pipeline_metrics(pipeline_name)
        save_json(paths["metrics"], metrics)
        summary[pipeline_name] = metrics
    save_json(SUMMARY_PATH, summary)
    return summary


def main() -> int:
    args = parse_args()
    if args.pipeline == "all":
        summary = write_all_metrics()
        for pipeline_name in DEFAULTS:
            print(f"Wrote metrics to {DEFAULTS[pipeline_name]['metrics']}.")
        print(f"Wrote summary metrics to {SUMMARY_PATH}.")
        print(
            "Summary counts: "
            + ", ".join(
                f"{name} personas={summary[name]['persona_count']} requirements={summary[name]['requirements_count']} tests={summary[name]['tests_count']}"
                for name in DEFAULTS
            )
        )
        return 0

    paths = DEFAULTS[args.pipeline]
    metrics = compute_pipeline_metrics(args.pipeline)
    save_json(paths["metrics"], metrics)
    print(f"Wrote metrics to {paths['metrics']}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
