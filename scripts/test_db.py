from twi.db.base import SessionLocal
from twi.db.repository import upsert_posts
from twi.ingestion.fetcher import fetch_subreddit_posts

session = SessionLocal()
posts = fetch_subreddit_posts("Teachers", after="2024-01-01", before="2024-02-01", limit=20)
count = upsert_posts(session, posts)
session.close()

print(f"Inserted {count} posts")