import json
from pathlib import Path
from datetime import datetime, timezone

from twi.db.base import SessionLocal
from twi.db.models import Post
from twi.nlp import clean_for_keywords_batch
from twi.logging_config import get_logger

logger = get_logger(__name__)

OUT_DIR = Path("data/topics")
OUT_DIR.mkdir(parents=True, exist_ok=True)


def to_year(value) -> int:
    if isinstance(value, datetime):
        return value.year
    return datetime.fromtimestamp(value, tz=timezone.utc).year


def main():
    logger.info("Streaming posts from Postgres")
    session = SessionLocal()
    posts_by_year: dict[int, list[int]] = {}
    raw_by_id: dict[int, tuple[str, str]] = {}

    count = 0
    query = session.query(Post.id, Post.title, Post.body, Post.created_utc).yield_per(5000)
    for post_id, title, body, created_utc in query:
        body = body or ""
        raw_by_id[post_id] = (title, body)
        year = to_year(created_utc)
        posts_by_year.setdefault(year, []).append(post_id)
        count += 1
        if count % 50000 == 0:
            logger.info(f"Streamed {count} posts")
    session.close()
    logger.info(f"Finished streaming {count} posts across {len(posts_by_year)} years")

    all_ids = list(raw_by_id.keys())
    combined_texts = [f"{raw_by_id[pid][0]}. {raw_by_id[pid][1]}" for pid in all_ids]

    logger.info("Cleaning text for keyword extraction (batched)")
    cleaned = clean_for_keywords_batch(combined_texts, batch_size=200)
    logger.info("Finished cleaning text")

    keyword_texts = dict(zip(all_ids, cleaned))
    raw_texts = {pid: f"{raw_by_id[pid][0]}\n{raw_by_id[pid][1]}"[:300] for pid in all_ids}

    logger.info("Saving cached text to disk")
    with open(OUT_DIR / "keyword_texts.json", "w", encoding="utf-8") as f:
        json.dump(keyword_texts, f)
    with open(OUT_DIR / "raw_texts.json", "w", encoding="utf-8") as f:
        json.dump(raw_texts, f)
    with open(OUT_DIR / "posts_by_year.json", "w", encoding="utf-8") as f:
        json.dump(posts_by_year, f)

    logger.info("Done. Text cache saved to data/topics/")


if __name__ == "__main__":
    main()