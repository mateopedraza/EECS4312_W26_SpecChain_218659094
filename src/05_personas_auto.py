"""Build automated review groups and personas."""

from __future__ import annotations

import argparse
import json
import re
import sys
from collections import Counter
from pathlib import Path
from typing import Any

from auto_pipeline_utils import (
    MODEL_NAME,
    groq_chat_json,
    load_jsonl,
    save_json,
    upsert_prompt_step,
)


ROOT = Path(__file__).resolve().parents[1]
INPUT_PATH = ROOT / "data" / "reviews_clean.jsonl"
OUTPUT_PATH = ROOT / "data" / "review_groups_auto.json"
PERSONAS_OUTPUT_PATH = ROOT / "personas" / "personas_auto.json"
PROMPT_PATH = ROOT / "prompts" / "prompt_auto.json"

INTERNAL_GROUP_ORDER = [
    "billing",
    "stability",
    "playback",
    "sleep",
    "benefits",
]

GROUP_ID_MAP = {
    "billing": "A1",
    "stability": "A2",
    "playback": "A3",
    "sleep": "A4",
    "benefits": "A5",
}

PERSONA_ID_MAP = {
    "billing": "AP1",
    "stability": "AP2",
    "playback": "AP3",
    "sleep": "AP4",
    "benefits": "AP5",
}

GENERIC_TOKENS = {
    "app",
    "headspace",
    "really",
    "using",
    "used",
    "would",
    "could",
    "also",
    "still",
    "thing",
    "things",
    "many",
    "much",
    "make",
    "made",
    "need",
    "want",
    "dont",
    "doesnt",
    "cant",
    "ive",
    "im",
    "get",
    "got",
    "even",
    "time",
    "year",
    "month",
    "day",
    "one",
    "two",
    "good",
    "great",
    "love",
    "like",
    "help",
    "helpful",
    "content",
    "user",
    "users",
    "phone",
    "screen",
    "feature",
    "features",
    "option",
    "options",
    "please",
    "since",
    "every",
    "anything",
    "nothing",
    "something",
    "without",
    "within",
    "around",
    "always",
    "never",
    "lately",
    "recently",
    "issue",
    "issues",
    "problem",
    "problems",
    "service",
    "customer",
    "support",
    "work",
    "works",
    "working",
    "find",
    "everything",
    "back",
    "keep",
    "take",
    "life",
    "better",
    "daily",
    "session",
    "sessions",
    "minute",
    "minutes",
    "open",
    "trying",
    "try",
    "well",
    "lot",
    "thats",
    "there",
    "their",
    "theyre",
    "able",
    "look",
    "looking",
    "went",
    "going",
    "come",
    "comes",
    "needed",
    "needs",
    "makes",
    "way",
    "days",
    "years",
    "months",
    "today",
    "tomorrow",
    "yesterday",
    "right",
    "left",
    "next",
    "last",
    "first",
    "second",
    "third",
    "overall",
    "however",
    "though",
    "etc",
    "actually",
    "almost",
    "already",
    "maybe",
    "seems",
    "seem",
    "seemed",
    "must",
    "might",
    "enough",
    "quite",
    "little",
    "people",
    "start",
    "know",
    "give",
    "getting",
    "didnt",
    "wont",
    "tried",
}


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Automatically group cleaned reviews and label the groups with Groq."
    )
    parser.add_argument("--input", type=Path, default=INPUT_PATH)
    parser.add_argument("--output", type=Path, default=OUTPUT_PATH)
    parser.add_argument("--personas-output", type=Path, default=PERSONAS_OUTPUT_PATH)
    parser.add_argument("--prompt-output", type=Path, default=PROMPT_PATH)
    parser.add_argument("--model", default=MODEL_NAME)
    return parser.parse_args()


def tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9']+", text.lower()))


def lexical_tokens(text: str) -> list[str]:
    return [
        token
        for token in re.findall(r"[a-z0-9']+", text.lower())
        if len(token) >= 4 and token not in GENERIC_TOKENS and not token.isdigit()
    ]


def score_review(text: str, rating: int) -> tuple[dict[str, float], int]:
    tokens = tokenize(text)
    lower_text = text.lower()
    scores = {key: 0.0 for key in INTERNAL_GROUP_ORDER}
    positive_hits = 0

    def has_phrase(phrase: str) -> bool:
        return phrase in lower_text

    for token, weight in {
        "refund": 5,
        "charged": 5,
        "charge": 5,
        "trial": 4,
        "subscription": 4,
        "cancel": 4,
        "canceled": 4,
        "cancelled": 4,
        "payment": 4,
        "paywall": 4,
        "paid": 3,
        "paying": 3,
        "money": 2,
        "billing": 4,
        "renew": 3,
        "renewal": 3,
    }.items():
        if token in tokens:
            scores["billing"] += weight

    for phrase, weight in {
        "free trial": 5,
        "behind paywall": 5,
        "locked behind": 4,
        "charged full": 5,
        "cancel subscription": 5,
        "annual subscription": 3,
        "credit card": 4,
    }.items():
        if has_phrase(phrase):
            scores["billing"] += weight

    for token, weight in {
        "crash": 5,
        "crashing": 5,
        "freeze": 4,
        "freezing": 4,
        "load": 4,
        "loading": 4,
        "slow": 3,
        "bug": 3,
        "buggy": 3,
        "glitch": 3,
        "glitchy": 3,
        "unusable": 4,
        "error": 3,
        "update": 2,
        "google": 2,
        "account": 2,
        "email": 2,
    }.items():
        if token in tokens:
            scores["stability"] += weight

    for phrase, weight in {
        "wont load": 5,
        "slow load": 4,
        "latest update": 2,
        "recent update": 2,
        "force stop": 3,
        "load page": 3,
        "google fit": 4,
    }.items():
        if has_phrase(phrase):
            scores["stability"] += weight

    playback_issue_tokens = {
        "stop",
        "stopping",
        "paused",
        "pause",
        "pausing",
        "offline",
        "buffer",
        "buffering",
        "interrupted",
        "interrupt",
        "disconnect",
        "playback",
        "audio",
    }
    playback_context_tokens = {
        "meditation",
        "session",
        "sessions",
        "track",
        "tracks",
        "podcast",
        "podcasts",
        "content",
        "soundscape",
        "soundscapes",
        "music",
        "guided",
    }
    for token, weight in {
        "stop": 3,
        "stopping": 3,
        "paused": 3,
        "pause": 3,
        "pausing": 3,
        "offline": 4,
        "buffer": 4,
        "buffering": 4,
        "interrupted": 4,
        "disconnect": 4,
        "playback": 4,
        "audio": 2,
    }.items():
        if token in tokens:
            scores["playback"] += weight

    if tokens & playback_issue_tokens and tokens & playback_context_tokens:
        scores["playback"] += 4

    for phrase, weight in {
        "stop playing": 6,
        "middle meditation": 5,
        "mid meditation": 5,
        "oops something went wrong": 4,
        "playing podcasts": 3,
    }.items():
        if has_phrase(phrase):
            scores["playback"] += weight

    for token, weight in {
        "sleep": 2,
        "sleepcast": 7,
        "sleepcasts": 7,
        "bedtime": 5,
        "soundscape": 5,
        "soundscapes": 5,
        "insomnia": 4,
        "night": 2,
        "story": 1,
        "stories": 1,
    }.items():
        if token in tokens:
            scores["sleep"] += weight

    for phrase, weight in {
        "sleep cast": 7,
        "sleep story": 5,
        "fall asleep": 5,
        "sleep music": 4,
        "white noise": 4,
    }.items():
        if has_phrase(phrase):
            scores["sleep"] += weight

    if "sleep" in tokens and tokens & {
        "story",
        "stories",
        "music",
        "night",
        "bedtime",
        "soundscape",
        "soundscapes",
    }:
        scores["sleep"] += 4

    for token, weight in {
        "anxiety": 4,
        "stress": 4,
        "calm": 4,
        "helped": 4,
        "recommend": 3,
        "mindfulness": 4,
        "grief": 5,
        "focus": 3,
        "relaxing": 4,
        "worth": 2,
        "unwind": 4,
        "mental": 2,
        "health": 2,
        "amazing": 2,
    }.items():
        if token in tokens:
            scores["benefits"] += weight
            positive_hits += 1

    for phrase, weight in {
        "mental health": 4,
        "life changing": 5,
        "highly recommend": 4,
        "worth every penny": 4,
    }.items():
        if has_phrase(phrase):
            scores["benefits"] += weight
            positive_hits += 1

    if rating >= 4 and positive_hits:
        scores["benefits"] += 2

    negative_benefit_tokens = {
        "crash",
        "refund",
        "charged",
        "trial",
        "cancel",
        "subscription",
        "paywall",
        "load",
        "slow",
        "stop",
        "offline",
        "error",
        "freeze",
        "buggy",
        "unusable",
    }
    scores["benefits"] -= 1.5 * len(tokens & negative_benefit_tokens)

    return scores, positive_hits


def choose_group(review: dict[str, Any]) -> tuple[str, dict[str, float]]:
    text = review["text_clean"]
    rating = int(review["score"])
    scores, positive_hits = score_review(text, rating)

    if scores["sleep"] >= 6 and scores["sleep"] + 1 >= scores["billing"]:
        return "sleep", scores
    if (
        scores["playback"] >= 8
        and scores["playback"] >= scores["stability"]
        and scores["playback"] + 2 >= scores["billing"]
    ):
        return "playback", scores
    if scores["stability"] >= 6 and scores["stability"] + 1 >= scores["billing"]:
        return "stability", scores
    if (
        positive_hits
        and rating >= 4
        and scores["benefits"] >= 6
        and scores["benefits"]
        > max(
            scores["billing"],
            scores["stability"],
            scores["playback"],
            scores["sleep"],
        )
    ):
        return "benefits", scores
    if scores["billing"] >= 8:
        return "billing", scores
    if positive_hits and rating >= 4 and scores["benefits"] >= 4:
        return "benefits", scores
    if scores["stability"] >= scores["playback"] and scores["stability"] >= 4:
        return "stability", scores
    if scores["playback"] >= 4:
        return "playback", scores
    if rating >= 4 and positive_hits:
        return "benefits", scores
    if scores["billing"] > 0:
        return "billing", scores
    return "stability", scores


def assign_reviews(reviews: list[dict[str, Any]]) -> dict[str, list[dict[str, Any]]]:
    grouped: dict[str, list[dict[str, Any]]] = {key: [] for key in INTERNAL_GROUP_ORDER}
    for review in reviews:
        group_key, scores = choose_group(review)
        grouped[group_key].append(
            {
                "id": review["id"],
                "text_clean": review["text_clean"],
                "score": review["score"],
                "date": review["date"],
                "group_score": round(scores[group_key], 3),
            }
        )
    return grouped


def compute_top_terms(items: list[dict[str, Any]], limit: int = 10) -> list[str]:
    counter: Counter[str] = Counter()
    for item in items:
        counter.update(set(lexical_tokens(item["text_clean"])))
    return [term for term, _ in counter.most_common(limit)]


def compute_top_phrases(items: list[dict[str, Any]], limit: int = 8) -> list[str]:
    counter: Counter[str] = Counter()
    for item in items:
        tokens = lexical_tokens(item["text_clean"])
        phrases = {" ".join(pair) for pair in zip(tokens, tokens[1:])}
        counter.update(phrases)
    return [phrase for phrase, _ in counter.most_common(limit)]


def select_representative_items(
    items: list[dict[str, Any]], sample_size: int = 8
) -> list[dict[str, str]]:
    ranked = sorted(
        items,
        key=lambda item: (-float(item["group_score"]), item["id"]),
    )
    chosen = ranked[:sample_size]
    return [{"id": item["id"], "text": item["text_clean"]} for item in chosen]


def build_prompt_payload(grouped: dict[str, list[dict[str, Any]]]) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for key in INTERNAL_GROUP_ORDER:
        items = grouped[key]
        payload.append(
            {
                "cluster_key": key,
                "group_id": GROUP_ID_MAP[key],
                "review_count": len(items),
                "top_terms": compute_top_terms(items),
                "top_phrases": compute_top_phrases(items),
                "sample_reviews": select_representative_items(items),
            }
        )
    return payload


def build_grouping_prompts(cluster_payload: list[dict[str, Any]]) -> tuple[str, str]:
    system_prompt = (
        "You are a precise software review analyst. "
        "You will rename pre-grouped clusters of mobile app reviews. "
        "Do not change cluster membership. "
        "Use short natural language themes. "
        "Return valid JSON only."
    )

    user_prompt = (
        "We already grouped cleaned Headspace reviews into five fixed clusters using local lexical grouping.\n"
        "For each cluster, keep the same cluster_key and group_id, then produce:\n"
        "1. theme: a concise human readable theme\n"
        "2. example_review_ids: choose exactly 3 ids from the provided sample_reviews that best represent the cluster\n\n"
        "Return exactly this JSON shape:\n"
        "{\n"
        '  "groups": [\n'
        '    {\n'
        '      "cluster_key": "billing",\n'
        '      "group_id": "A1",\n'
        '      "theme": "Billing and refund complaints",\n'
        '      "example_review_ids": ["review_00001", "review_00022", "review_00185"]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Clusters:\n"
        f"{json.dumps(cluster_payload, indent=2, ensure_ascii=True)}"
    )
    return system_prompt, user_prompt


def validate_label_payload(payload: dict[str, Any]) -> dict[str, dict[str, Any]]:
    groups = payload.get("groups")
    if not isinstance(groups, list):
        raise RuntimeError("Groq output must contain a 'groups' list.")

    normalized: dict[str, dict[str, Any]] = {}
    for group in groups:
        if not isinstance(group, dict):
            continue
        cluster_key = group.get("cluster_key")
        theme = group.get("theme")
        example_review_ids = group.get("example_review_ids")
        if (
            cluster_key in INTERNAL_GROUP_ORDER
            and isinstance(theme, str)
            and isinstance(example_review_ids, list)
        ):
            normalized[cluster_key] = {
                "group_id": group.get("group_id", GROUP_ID_MAP[cluster_key]),
                "theme": theme.strip(),
                "example_review_ids": [
                    review_id for review_id in example_review_ids if isinstance(review_id, str)
                ],
            }

    missing = [key for key in INTERNAL_GROUP_ORDER if key not in normalized]
    if missing:
        raise RuntimeError(f"Groq output is missing clusters: {missing}")

    return normalized


def build_output_document(
    grouped: dict[str, list[dict[str, Any]]],
    labels: dict[str, dict[str, Any]],
) -> dict[str, Any]:
    groups = []
    for key in INTERNAL_GROUP_ORDER:
        items = grouped[key]
        item_lookup = {item["id"]: item["text_clean"] for item in items}
        picked_ids = labels[key]["example_review_ids"]
        filtered_ids = [review_id for review_id in picked_ids if review_id in item_lookup][:3]
        if len(filtered_ids) < 3:
            raise RuntimeError(
                f"Groq output for group {GROUP_ID_MAP[key]} must include 3 valid example_review_ids."
            )

        groups.append(
            {
                "group_id": GROUP_ID_MAP[key],
                "theme": labels[key]["theme"],
                "review_ids": [item["id"] for item in items],
                "example_reviews": [item_lookup[review_id] for review_id in filtered_ids],
            }
        )
    return {"groups": groups}


def build_persona_prompt_payload(
    grouped: dict[str, list[dict[str, Any]]],
    labels: dict[str, dict[str, Any]],
) -> list[dict[str, Any]]:
    payload: list[dict[str, Any]] = []
    for key in INTERNAL_GROUP_ORDER:
        items = grouped[key]
        payload.append(
            {
                "persona_id": PERSONA_ID_MAP[key],
                "group_id": GROUP_ID_MAP[key],
                "theme": labels[key]["theme"],
                "review_count": len(items),
                "top_terms": compute_top_terms(items, limit=8),
                "sample_reviews": select_representative_items(items, sample_size=5),
            }
        )
    return payload


def build_persona_prompts(persona_payload: list[dict[str, Any]]) -> tuple[str, str]:
    system_prompt = (
        "You are a product analyst creating structured personas from grouped software reviews. "
        "Create one persona per provided review group. "
        "Use grounded language and only return valid JSON."
    )

    user_prompt = (
        "Create exactly one persona for each provided group.\n"
        "Keep the given persona_id and derived_from_group exactly as provided.\n"
        "Return JSON only using this shape:\n"
        "{\n"
        '  "personas": [\n'
        "    {\n"
        '      "id": "AP1",\n'
        '      "name": "Example Persona Name",\n'
        '      "description": "One sentence summary of the user.",\n'
        '      "derived_from_group": "A1",\n'
        '      "goals": ["goal 1", "goal 2", "goal 3"],\n'
        '      "pain_points": ["pain 1", "pain 2", "pain 3"],\n'
        '      "context": ["context 1", "context 2", "context 3"],\n'
        '      "constraints": ["constraint 1", "constraint 2", "constraint 3"],\n'
        '      "evidence_reviews": ["review_00001", "review_00022", "review_00185"]\n'
        "    }\n"
        "  ]\n"
        "}\n\n"
        "Groups:\n"
        f"{json.dumps(persona_payload, indent=2, ensure_ascii=True)}"
    )
    return system_prompt, user_prompt


def validate_persona_payload(payload: dict[str, Any]) -> list[dict[str, Any]]:
    personas = payload.get("personas")
    if not isinstance(personas, list):
        raise RuntimeError("Persona output must contain a 'personas' list.")

    normalized: list[dict[str, Any]] = []
    seen = set()
    valid_group_ids = set(GROUP_ID_MAP.values())
    for persona in personas:
        if not isinstance(persona, dict):
            continue
        persona_id = persona.get("id")
        name = persona.get("name")
        description = persona.get("description")
        derived_from_group = persona.get("derived_from_group")
        if (
            not isinstance(persona_id, str)
            or not isinstance(name, str)
            or not isinstance(description, str)
            or derived_from_group not in valid_group_ids
            or persona_id in seen
        ):
            continue
        seen.add(persona_id)
        normalized.append(
            {
                "id": persona_id,
                "name": name.strip(),
                "description": description.strip(),
                "derived_from_group": derived_from_group,
                "goals": [value for value in persona.get("goals", []) if isinstance(value, str)],
                "pain_points": [
                    value for value in persona.get("pain_points", []) if isinstance(value, str)
                ],
                "context": [value for value in persona.get("context", []) if isinstance(value, str)],
                "constraints": [
                    value for value in persona.get("constraints", []) if isinstance(value, str)
                ],
                "evidence_reviews": [
                    value
                    for value in persona.get("evidence_reviews", [])
                    if isinstance(value, str)
                ],
            }
        )

    if len(normalized) != len(INTERNAL_GROUP_ORDER):
        raise RuntimeError("Persona output must include one valid persona for each auto group.")
    return normalized


def main() -> int:
    args = parse_args()
    reviews = load_jsonl(args.input)
    grouped = assign_reviews(reviews)
    cluster_payload = build_prompt_payload(grouped)
    grouping_system_prompt, grouping_user_prompt = build_grouping_prompts(cluster_payload)
    upsert_prompt_step(
        args.prompt_output,
        "review_grouping",
        args.model,
        grouping_system_prompt,
        grouping_user_prompt,
    )

    raw_labels = groq_chat_json(args.model, grouping_system_prompt, grouping_user_prompt)
    labels = validate_label_payload(raw_labels)
    output_payload = build_output_document(grouped, labels)
    save_json(args.output, output_payload)

    persona_payload = build_persona_prompt_payload(grouped, labels)
    persona_system_prompt, persona_user_prompt = build_persona_prompts(persona_payload)
    upsert_prompt_step(
        args.prompt_output,
        "persona_generation",
        args.model,
        persona_system_prompt,
        persona_user_prompt,
    )

    raw_personas = groq_chat_json(args.model, persona_system_prompt, persona_user_prompt)
    personas_output = {"personas": validate_persona_payload(raw_personas)}
    save_json(args.personas_output, personas_output)

    total_reviews = sum(len(grouped[key]) for key in INTERNAL_GROUP_ORDER)
    print(f"Wrote {len(output_payload['groups'])} groups covering {total_reviews} reviews.")
    for group in output_payload["groups"]:
        print(f"{group['group_id']}: {group['theme']} ({len(group['review_ids'])} reviews)")
    print(f"Wrote {len(personas_output['personas'])} personas.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
