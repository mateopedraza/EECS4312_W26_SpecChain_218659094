"""Helpers shared across the automated pipeline scripts."""

from __future__ import annotations

import json
import os
import re
import sys
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
MODEL_NAME = "meta-llama/llama-4-scout-17b-16e-instruct"
API_URL = "https://api.groq.com/openai/v1/chat/completions"
USER_AGENT = (
    "SpecChain-AutoPipeline/1.0 "
    f"(Python/{sys.version_info.major}.{sys.version_info.minor}; urllib)"
)


def load_json(path: Path, default: Any = None) -> Any:
    if not path.exists():
        return default
    return json.loads(path.read_text(encoding="utf-8"))


def save_json(path: Path, payload: Any) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, ensure_ascii=True), encoding="utf-8")


def load_jsonl(path: Path) -> list[dict[str, Any]]:
    rows: list[dict[str, Any]] = []
    with path.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                rows.append(json.loads(line))
    return rows


def parse_json_object(raw_text: str) -> dict[str, Any]:
    raw_text = raw_text.strip()
    if raw_text.startswith("```"):
        raw_text = re.sub(r"^```(?:json)?", "", raw_text).strip()
        raw_text = re.sub(r"```$", "", raw_text).strip()

    first_brace = raw_text.find("{")
    last_brace = raw_text.rfind("}")
    if first_brace == -1 or last_brace == -1:
        raise RuntimeError(f"Could not find JSON object in model response: {raw_text}")

    candidate = raw_text[first_brace : last_brace + 1]
    try:
        return json.loads(candidate)
    except json.JSONDecodeError as exc:
        raise RuntimeError(f"Model returned invalid JSON: {candidate}") from exc


def groq_chat_json(model: str, system_prompt: str, user_prompt: str) -> dict[str, Any]:
    api_key = os.getenv("GROQ_API_KEY")
    if not api_key:
        raise RuntimeError(
            "GROQ_API_KEY is not set in this shell. Export it before running the automated pipeline."
        )

    payload = {
        "model": model,
        "temperature": 0,
        "messages": [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_prompt},
        ],
    }

    request = urllib.request.Request(
        API_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
            "Accept": "application/json",
            "User-Agent": USER_AGENT,
        },
        method="POST",
    )

    try:
        with urllib.request.urlopen(request, timeout=120) as response:
            body = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        detail = exc.read().decode("utf-8", errors="replace")
        if "error code: 1010" in detail.lower():
            raise RuntimeError(
                "Groq API request failed with HTTP 403 and Cloudflare error 1010. "
                "This usually means the request was blocked before it reached the API. "
                "The helper now sends a custom User-Agent, so rerun the script. "
                "If it still fails, try without VPN or Private Relay, or from a different network."
            ) from exc
        raise RuntimeError(f"Groq API request failed: {detail}") from exc
    except urllib.error.URLError as exc:
        raise RuntimeError(f"Groq API connection failed: {exc}") from exc

    try:
        content = body["choices"][0]["message"]["content"]
    except (KeyError, IndexError, TypeError) as exc:
        raise RuntimeError(f"Unexpected Groq response shape: {body}") from exc

    return parse_json_object(content)


def upsert_prompt_step(
    path: Path,
    step_name: str,
    model: str,
    system_prompt: str,
    user_prompt: str,
    temperature: float = 0,
) -> None:
    existing = load_json(path, default={}) or {}

    steps = existing.get("steps")
    if not isinstance(steps, dict):
        steps = {}
        if "system_prompt" in existing or "user_prompt" in existing:
            steps["review_grouping"] = {
                "model": existing.get("model", model),
                "temperature": existing.get("temperature", temperature),
                "system_prompt": existing.get("system_prompt", ""),
                "user_prompt": existing.get("user_prompt", ""),
            }

    steps[step_name] = {
        "model": model,
        "temperature": temperature,
        "system_prompt": system_prompt,
        "user_prompt": user_prompt,
    }

    payload = {
        "model": model,
        "steps": steps,
    }
    save_json(path, payload)
