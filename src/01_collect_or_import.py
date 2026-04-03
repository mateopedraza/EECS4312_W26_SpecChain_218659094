"""Collect raw Headspace reviews from Google Play."""

import json
import time

APP_ID = "com.getsomeheadspace.android"
OUTPUT_PATH = "data/reviews_raw.jsonl"

def collect_reviews():
    try:
        from google_play_scraper import Sort, reviews
    except ModuleNotFoundError as exc:
        raise RuntimeError(
            "google_play_scraper is required to recollect raw reviews. "
            "Install it before running src/01_collect_or_import.py."
        ) from exc

    all_reviews = []
    continuation_token = None
    target = 5000

    print(f"Collecting reviews for {APP_ID}...")

    while len(all_reviews) < target:
        batch, continuation_token = reviews(
            APP_ID,
            lang='en',
            country='us',
            sort=Sort.NEWEST,
            count=200,
            continuation_token=continuation_token
        )
        if not batch:
            break
        all_reviews.extend(batch)
        print(f"  Collected {len(all_reviews)} reviews so far...")
        if not continuation_token:
            break
        time.sleep(1)

    print(f"Total collected: {len(all_reviews)}")

    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for i, r in enumerate(all_reviews):
            record = {
                "id": f"review_{i+1:05d}",
                "text": r.get("content", ""),
                "score": r.get("score"),
                "date": str(r.get("at", ""))
            }
            f.write(json.dumps(record) + "\n")

    print(f"Saved to {OUTPUT_PATH}")

if __name__ == "__main__":
    collect_reviews()
