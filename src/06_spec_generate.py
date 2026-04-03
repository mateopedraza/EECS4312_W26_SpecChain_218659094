"""Generate automated requirements from personas."""

from __future__ import annotations

import argparse
from pathlib import Path
from typing import Any

from auto_pipeline_utils import MODEL_NAME, groq_chat_json, load_json, upsert_prompt_step


ROOT = Path(__file__).resolve().parents[1]
PERSONAS_PATH = ROOT / "personas" / "personas_auto.json"
SPEC_PATH = ROOT / "spec" / "spec_auto.md"
PROMPT_PATH = ROOT / "prompts" / "prompt_auto.json"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Generate automated requirements from personas.")
    parser.add_argument("--input", type=Path, default=PERSONAS_PATH)
    parser.add_argument("--output", type=Path, default=SPEC_PATH)
    parser.add_argument("--prompt-output", type=Path, default=PROMPT_PATH)
    parser.add_argument("--model", default=MODEL_NAME)
    return parser.parse_args()


def build_spec_prompt_payload(personas: list[dict[str, Any]]) -> list[dict[str, Any]]:
    payload = []
    for persona in personas:
        payload.append(
            {
                "persona_id": persona["id"],
                "name": persona["name"],
                "description": persona["description"],
                "derived_from_group": persona["derived_from_group"],
                "goals": persona["goals"],
                "pain_points": persona["pain_points"],
                "context": persona["context"],
                "constraints": persona["constraints"],
            }
        )
    return payload


def build_prompts(persona_payload: list[dict[str, Any]]) -> tuple[str, str]:
    system_prompt = (
        "You are a software requirements analyst. "
        "Write clear and testable functional requirements from personas. "
        "Return valid JSON only."
    )

    user_prompt = (
        "Create exactly 15 requirements from the personas below. "
        "Make 3 requirements per persona.\n"
        "Return JSON only using this shape:\n"
        "{\n"
        '  "requirements": [\n'
        "    {\n"
        '      "source_persona_id": "AP1",\n'
        '      "derived_from_group": "A1",\n'
        '      "description": "The app should ...",\n'
        '      "acceptance_criteria": "Given ... when ... then ..."\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Requirements should sound natural, be specific enough to test, and stay grounded in the persona goals and pain points.\n\n"
        "Personas:\n"
        f"{persona_payload}"
    )
    return system_prompt, user_prompt


def validate_requirements(
    raw_payload: dict[str, Any], personas: list[dict[str, Any]]
) -> list[dict[str, Any]]:
    raw_requirements = raw_payload.get("requirements")
    if not isinstance(raw_requirements, list):
        raise RuntimeError("Requirement payload must contain a 'requirements' list.")

    persona_ids = {persona["id"] for persona in personas}
    group_ids = {persona["derived_from_group"] for persona in personas}
    normalized: list[dict[str, Any]] = []
    for requirement in raw_requirements:
        if not isinstance(requirement, dict):
            continue
        source_persona_id = requirement.get("source_persona_id")
        derived_from_group = requirement.get("derived_from_group")
        description = requirement.get("description")
        acceptance_criteria = requirement.get("acceptance_criteria")
        if (
            source_persona_id in persona_ids
            and derived_from_group in group_ids
            and isinstance(description, str)
            and isinstance(acceptance_criteria, str)
        ):
            normalized.append(
                {
                    "source_persona_id": source_persona_id,
                    "derived_from_group": derived_from_group,
                    "description": description.strip(),
                    "acceptance_criteria": acceptance_criteria.strip(),
                }
            )

    if len(normalized) < 10:
        raise RuntimeError("At least 10 valid requirements are required.")
    return normalized[:15]


def format_spec_markdown(
    requirements: list[dict[str, Any]], personas: list[dict[str, Any]]
) -> str:
    persona_lookup = {persona["id"]: persona for persona in personas}
    blocks = []
    for index, requirement in enumerate(requirements, start=1):
        persona = persona_lookup[requirement["source_persona_id"]]
        blocks.append(
            "\n".join(
                [
                    f"# Requirement ID: FR_auto_{index}",
                    f"- Description: [{requirement['description']}]",
                    f"- Source Persona: [{persona['name']}]",
                    f"- Traceability: [Derived from persona {persona['id']}, which originated from review group {requirement['derived_from_group']}]",
                    f"- Acceptance Criteria: [{requirement['acceptance_criteria']}]",
                ]
            )
        )
    return "\n\n".join(blocks) + "\n"


def main() -> int:
    args = parse_args()
    personas_payload = load_json(args.input, default={}) or {}
    personas = personas_payload.get("personas", [])
    if not personas:
        raise RuntimeError("No personas found. Run src/05_personas_auto.py first.")

    prompt_payload = build_spec_prompt_payload(personas)
    system_prompt, user_prompt = build_prompts(prompt_payload)
    upsert_prompt_step(
        args.prompt_output,
        "spec_generation",
        args.model,
        system_prompt,
        user_prompt,
    )

    raw_payload = groq_chat_json(args.model, system_prompt, user_prompt)
    validated = validate_requirements(raw_payload, personas)
    markdown = format_spec_markdown(validated, personas)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(markdown, encoding="utf-8")
    print(f"Wrote {len(validated)} automated requirements to {args.output}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
