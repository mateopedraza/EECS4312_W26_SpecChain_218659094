import json
import re
import nltk
from nltk.corpus import stopwords
from nltk.stem import WordNetLemmatizer

nltk.download('stopwords', quiet=True)
nltk.download('wordnet', quiet=True)
nltk.download('omit', quiet=True)

RAW_PATH = "data/reviews_raw.jsonl"
CLEAN_PATH = "data/reviews_clean.jsonl"
META_PATH = "data/dataset_metadata.json"

def clean_text(text):
    text = text.lower()
    text = text.encode('ascii', 'ignore').decode()         # remove emojis/special chars
    text = re.sub(r'[^a-z0-9\s]', '', text)               # remove punctuation
    text = re.sub(r'\d+', lambda m: str(m.group()), text)  # keep numbers as text
    text = re.sub(r'\s+', ' ', text).strip()               # remove extra whitespace

    stop_words = set(stopwords.words('english'))
    lemmatizer = WordNetLemmatizer()
    tokens = text.split()
    tokens = [lemmatizer.lemmatize(w) for w in tokens if w not in stop_words]
    return ' '.join(tokens)

def clean_reviews():
    raw_reviews = []
    with open(RAW_PATH, "r", encoding="utf-8") as f:
        for line in f:
            raw_reviews.append(json.loads(line))

    seen_texts = set()
    cleaned = []

    for r in raw_reviews:
        text = r.get("text", "").strip()
        if not text or len(text) < 10:     # skip empty/very short
            continue
        cleaned_text = clean_text(text)
        if cleaned_text in seen_texts:     # skip duplicates
            continue
        seen_texts.add(cleaned_text)
        cleaned.append({
            "id": r["id"],
            "text_clean": cleaned_text,
            "score": r.get("score"),
            "date": r.get("date")
        })

    with open(CLEAN_PATH, "w", encoding="utf-8") as f:
        for r in cleaned:
            f.write(json.dumps(r) + "\n")

    metadata = {
        "app_name": "Headspace",
        "app_id": "com.getsomeheadspace.android",
        "raw_count": len(raw_reviews),
        "clean_count": len(cleaned),
        "collection_method": "google-play-scraper Python library",
        "cleaning_steps": [
            "Removed reviews under 10 characters",
            "Removed duplicates",
            "Lowercased all text",
            "Removed emojis and special characters",
            "Removed punctuation",
            "Removed extra whitespace",
            "Removed English stopwords",
            "Lemmatized tokens"
        ]
    }

    with open(META_PATH, "w") as f:
        json.dump(metadata, f, indent=2)

    print(f"Cleaned: {len(cleaned)} reviews saved to {CLEAN_PATH}")
    print(f"Metadata saved to {META_PATH}")

if __name__ == "__main__":
    clean_reviews()