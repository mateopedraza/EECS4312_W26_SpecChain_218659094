"""Clean raw reviews into the project JSONL format.

By default this keeps the committed clean dataset unless --rebuild is used.
"""

from __future__ import annotations

import argparse
import json
import re
from pathlib import Path

try:
    import nltk
    from nltk.corpus import stopwords
    from nltk.stem import WordNetLemmatizer
except ModuleNotFoundError:  
    nltk = None
    stopwords = None
    WordNetLemmatizer = None


ROOT = Path(__file__).resolve().parents[1]
RAW_PATH = ROOT / "data" / "reviews_raw.jsonl"
CLEAN_PATH = ROOT / "data" / "reviews_clean.jsonl"
META_PATH = ROOT / "data" / "dataset_metadata.json"

FALLBACK_STOPWORDS = {
    "a",
    "an",
    "and",
    "are",
    "as",
    "at",
    "be",
    "been",
    "being",
    "but",
    "by",
    "for",
    "from",
    "had",
    "has",
    "have",
    "he",
    "her",
    "here",
    "hers",
    "him",
    "his",
    "i",
    "if",
    "in",
    "into",
    "is",
    "it",
    "its",
    "itself",
    "me",
    "more",
    "most",
    "my",
    "myself",
    "no",
    "nor",
    "not",
    "of",
    "on",
    "once",
    "only",
    "or",
    "other",
    "our",
    "ours",
    "ourselves",
    "out",
    "own",
    "same",
    "she",
    "should",
    "so",
    "some",
    "such",
    "than",
    "that",
    "the",
    "their",
    "theirs",
    "them",
    "themselves",
    "then",
    "these",
    "they",
    "this",
    "those",
    "through",
    "to",
    "too",
    "under",
    "until",
    "up",
    "very",
    "was",
    "we",
    "were",
    "what",
    "when",
    "where",
    "which",
    "while",
    "who",
    "whom",
    "why",
    "with",
    "you",
    "your",
    "yours",
    "yourself",
    "yourselves",
}


class IdentityLemmatizer:

    def lemmatize(self, token: str) -> str:
        return token


def load_stopwords_and_lemmatizer() -> tuple[set[str], object, str]:
    if nltk is None or stopwords is None or WordNetLemmatizer is None:
        return FALLBACK_STOPWORDS, IdentityLemmatizer(), "fallback"

    for package_name in ("stopwords", "wordnet"):
        try:
            nltk.data.find(f"corpora/{package_name}")
        except LookupError: 
            nltk.download(package_name, quiet=True)

    try:
        stop_words = set(stopwords.words("english"))
        lemmatizer = WordNetLemmatizer()
        return stop_words, lemmatizer, "nltk"
    except LookupError: 
        return FALLBACK_STOPWORDS, IdentityLemmatizer(), "fallback"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Clean raw reviews into reviews_clean.jsonl.")
    parser.add_argument(
        "--rebuild",
        action="store_true",
        help="Rebuild the cleaned dataset from reviews_raw.jsonl.",
    )
    return parser.parse_args()


def clean_text(text: str, stop_words: set[str], lemmatizer: object) -> str:
    text = text.lower()
    text = text.encode("ascii", "ignore").decode()
    text = re.sub(r"[^a-z0-9\s]", "", text)
    text = re.sub(r"\s+", " ", text).strip()

    tokens = text.split()
    cleaned_tokens = [
        lemmatizer.lemmatize(token) for token in tokens if token and token not in stop_words
    ]
    return " ".join(cleaned_tokens)


def clean_reviews(rebuild: bool = False) -> None:
    if not RAW_PATH.exists():
        raise FileNotFoundError(f"Raw dataset not found: {RAW_PATH}")

    stop_words, lemmatizer, backend = load_stopwords_and_lemmatizer()

    if not rebuild and CLEAN_PATH.exists() and META_PATH.exists():
        print(f"Using existing cleaned dataset: {CLEAN_PATH}")
        print(f"Using existing metadata file: {META_PATH}")
        print(f"Cleaning backend: {backend}")
        return

    raw_reviews: list[dict[str, object]] = []
    with RAW_PATH.open("r", encoding="utf-8") as handle:
        for line in handle:
            if line.strip():
                raw_reviews.append(json.loads(line))

    seen_texts: set[str] = set()
    cleaned: list[dict[str, object]] = []

    for review in raw_reviews:
        text = str(review.get("text", "")).strip()
        if not text or len(text) < 10:
            continue

        cleaned_text = clean_text(text, stop_words, lemmatizer)
        if not cleaned_text or cleaned_text in seen_texts:
            continue

        seen_texts.add(cleaned_text)
        cleaned.append(
            {
                "id": review["id"],
                "text_clean": cleaned_text,
                "score": review.get("score"),
                "date": review.get("date"),
            }
        )

    CLEAN_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CLEAN_PATH.open("w", encoding="utf-8") as handle:
        for row in cleaned:
            handle.write(json.dumps(row) + "\n")

    metadata = {
        "app_name": "Headspace",
        "app_id": "com.getsomeheadspace.android",
        "raw_count": len(raw_reviews),
        "clean_count": len(cleaned),
        "collection_method": "google-play-scraper Python library",
        "cleaning_backend": backend,
        "cleaning_steps": [
            "Removed reviews under 10 characters",
            "Removed duplicates",
            "Lowercased all text",
            "Removed emojis and special characters",
            "Removed punctuation",
            "Removed extra whitespace",
            "Removed English stopwords",
            "Applied lemmatization when available",
        ],
    }

    META_PATH.write_text(json.dumps(metadata, indent=2), encoding="utf-8")
    print(f"Cleaned: {len(cleaned)} reviews saved to {CLEAN_PATH}")
    print(f"Metadata saved to {META_PATH}")
    print(f"Cleaning backend: {backend}")


if __name__ == "__main__":
    args = parse_args()
    clean_reviews(rebuild=args.rebuild)
