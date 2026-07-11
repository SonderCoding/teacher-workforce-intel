import argparse
from datetime import datetime, timezone
from twi.db.base import SessionLocal
from twi.db.repository import upsert_posts
from twi.ingestion.fetcher import fetch_subreddit_posts
from twi.logging_config import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

SUBREDDIT = "Teachers"

YEARS = [
    ("2017-01-01", "2018-01-01"),
    ("2018-01-01", "2019-01-01"),
    ("2019-01-01", "2020-01-01"),
    ("2020-01-01", "2021-01-01"),
    ("2021-01-01", "2022-01-01"),
    ("2022-01-01", "2023-01-01"),
    ("2023-01-01", "2024-01-01"),
    ("2024-01-01", "2025-01-01"),
    ("2025-01-01", "2026-01-01"),
]

POSTS_PER_YEAR = 10000


def run() -> None:
    session = SessionLocal()
    try:
        total = 0
        for after, before in YEARS:
            posts = fetch_subreddit_posts(
                SUBREDDIT, after=after, before=before, limit=POSTS_PER_YEAR
            )
            posts = [p for p in posts if len(p.body) > 50 or len(p.title) > 10]
            inserted = upsert_posts(session, posts)
            total += inserted
            log.info("Year %s: fetched %d posts, upserted %d", after[:4], len(posts), inserted)
        log.info("Total upserted: %d", total)
    finally:
        session.close()


if __name__ == "__main__":
    run()