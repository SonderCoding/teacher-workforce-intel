from datetime import datetime, timezone
from twi.db.base import SessionLocal
from twi.db.repository import upsert_posts
from twi.ingestion.fetcher import fetch_subreddit_posts
from twi.logging_config import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

SUBREDDIT = "Teachers"


def run() -> None:
    start_year = int(input("Start year (e.g. 2017): ").strip())
    end_year = int(input("End year inclusive (e.g. 2025): ").strip())
    posts_per_year = int(input("Posts per year (e.g. 10000): ").strip())

    years = [
        (f"{year}-01-01", f"{year + 1}-01-01")
        for year in range(start_year, end_year + 1)
    ]

    session = SessionLocal()
    try:
        total = 0
        for after, before in years:
            posts = fetch_subreddit_posts(
                SUBREDDIT, after=after, before=before, limit=posts_per_year
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