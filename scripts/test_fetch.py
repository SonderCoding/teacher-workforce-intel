# scripts/test_fetch.py
from twi.ingestion.fetcher import fetch_subreddit_posts

posts = fetch_subreddit_posts("Teachers", after="2024-09-01", before="2024-09-30", limit=20)
for p in posts:
    print(p.score, p.created_utc.date(), p.title[:80])