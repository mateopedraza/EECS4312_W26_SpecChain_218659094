"""Generate automated tests from the automated spec."""

from __future__ import annotations

import argparse
import re
from pathlib import Path
from typing import Any

from auto_pipeline_utils import MODEL_NAME, groq_chat_json, save_json, upsert_prompt_step


ROOT = Path(__file__).resolve().parents[1]
SPEC_PATH = ROOT / "spec" / "spec_auto.md"
TESTS_PATH = ROOT / "tests" / "tests_auto.json"
PROMPT_PATH = ROOT / "prompts" / "prompt_auto.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate automated validation tests.")
    parser.add_argument("--input", type=Path, default=SPEC_PATH)
    parser.add_argument("--output", type=Path, default=TESTS_PATH)
    parser.add_argument("--prompt-output", type=Path, default=PROMPT_PATH)
    parser.add_argument("--model", default=MODEL_NAME)
    return parser.parse_args()


def parse_requirements(path: Path) -> list[dict[str, str]]:
    text = path.read_text(encoding="utf-8")
    raw_blocks = re.split(r"(?m)^# Requirement ID: ", text)[1:]
    requirements: list[dict[str, str]] = []
    for block in raw_blocks:
        lines = block.strip().splitlines()
        requirement_id = lines[0].strip()
        description = ""
        source_persona = ""
        traceability = ""
        acceptance_criteria = ""
        for line in lines[1:]:
            if line.startswith("- Description: ["):
                description = line[len("- Description: [") : -1]
            elif line.startswith("- Source Persona: ["):
                source_persona = line[len("- Source Persona: [") : -1]
            elif line.startswith("- Traceability: ["):
                traceability = line[len("- Traceability: [") : -1]
            elif line.startswith("- Acceptance Criteria: ["):
                acceptance_criteria = line[len("- Acceptance Criteria: [") : -1]
        requirements.append(
            {
                "requirement_id": requirement_id,
                "description": description,
                "source_persona": source_persona,
                "traceability": traceability,
                "acceptance_criteria": acceptance_criteria,
            }
        )
    return requirements


def build_prompt_payload(requirements: list[dict[str, str]]) -> list[dict[str, str]]:
    return requirements


def chunk_requirements(
    requirements: list[dict[str, str]], chunk_size: int = 5
) -> list[list[dict[str, str]]]:
    return [requirements[index : index + chunk_size] for index in range(0, len(requirements), chunk_size)]


def build_prompts(requirement_payload: list[dict[str, str]]) -> tuple[str, str]:
    system_prompt = (
        "You are a QA analyst writing structured validation scenarios from requirements. "
        "Return valid JSON only."
    )
    user_prompt = (
        "Create exactly 2 validation tests for each requirement in this batch.\n"
        "Return JSON only using this shape:\n"
        "{\n"
        '  "tests": [\n'
        "    {\n"
        '      "requirement_id": "FR_auto_1",\n'
        '      "scenario": "Short scenario name",\n'
        '      "steps": ["step 1", "step 2", "step 3"],\n'
        '      "expected_result": "Expected outcome"\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Write clear test steps, keep steps short, and keep every test linked to the right requirement.\n\n"
        f"Requirements:\n{requirement_payload}"
    )
    return system_prompt, user_prompt


def validate_tests(raw_payload: dict[str, Any], requirements: list[dict[str, str]]) -> list[dict[str, Any]]:
    raw_tests = raw_payload.get("tests")
    if not isinstance(raw_tests, list):
        raise RuntimeError("Test payload must contain a 'tests' list.")

    valid_requirement_ids = {requirement["requirement_id"] for requirement in requirements}
    normalized: list[dict[str, Any]] = []
    for test in raw_tests:
        if not isinstance(test, dict):
            continue
        requirement_id = test.get("requirement_id")
        scenario = test.get("scenario")
        steps = test.get("steps")
        expected_result = test.get("expected_result")
        if (
            requirement_id in valid_requirement_ids
            and isinstance(scenario, str)
            and isinstance(steps, list)
            and isinstance(expected_result, str)
        ):
            cleaned_steps = [step for step in steps if isinstance(step, str)]
            if cleaned_steps:
                normalized.append(
                    {
                        "requirement_id": requirement_id,
                        "scenario": scenario.strip(),
                        "steps": cleaned_steps,
                        "expected_result": expected_result.strip(),
                    }
                )

    coverage = {test["requirement_id"] for test in normalized}
    missing = valid_requirement_ids - coverage
    if missing:
        raise RuntimeError(f"Missing tests for requirements: {sorted(missing)}")
    return normalized


def add_test_ids(tests: list[dict[str, Any]]) -> dict[str, Any]:
    payload = {"tests": []}
    for index, test in enumerate(tests, start=1):
        payload["tests"].append(
            {
                "test_id": f"T_auto_{index:03d}",
                "requirement_id": test["requirement_id"],
                "scenario": test["scenario"],
                "steps": test["steps"],
                "expected_result": test["expected_result"],
            }
        )
    return payload


def main() -> int:
    args = parse_args()
    requirements = parse_requirements(args.input)
    if not requirements:
        raise RuntimeError("No requirements found. Run src/06_spec_generate.py first.")

    chunks = chunk_requirements(requirements)
    first_prompt_payload = build_prompt_payload(chunks[0])
    first_system_prompt, first_user_prompt = build_prompts(first_prompt_payload)
    upsert_prompt_step(
        args.prompt_output,
        "test_generation",
        args.model,
        first_system_prompt,
        first_user_prompt,
    )

    validated: list[dict[str, Any]] = []
    for chunk in chunks:
        prompt_payload = build_prompt_payload(chunk)
        system_prompt, user_prompt = build_prompts(prompt_payload)
        raw_payload = groq_chat_json(args.model, system_prompt, user_prompt)
        validated.extend(validate_tests(raw_payload, chunk))

    payload = add_test_ids(validated)
    save_json(args.output, payload)
    print(f"Wrote {len(payload['tests'])} automated tests to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
