# tests/unit/test_fetcher.py
from unittest.mock import patch
from twi.ingestion.fetcher import fetch_subreddit_posts

FAKE_POST = {
    "id": "abc123",
    "title": "I am so burnt out",
    "selftext": "Teaching is hard.",
    "author": "teacher_anon",
    "score": 142,
    "num_comments": 38,
    "created_utc": "1725148800",
    "permalink": "/r/Teachers/comments/abc123/",
}

def test_fetch_returns_posts_on_single_page():
    with patch("twi.ingestion.fetcher.search_posts", return_value=[FAKE_POST]) as mock_search:
        posts = fetch_subreddit_posts("Teachers", after="2024-09-01", before="2024-09-30", limit=10)
    assert len(posts) == 1
    assert posts[0].reddit_id == "abc123"
    assert posts[0].score == 142

def test_fetch_handles_empty_response():
    with patch("twi.ingestion.fetcher.search_posts", return_value=[]):
        posts = fetch_subreddit_posts("Teachers", after="2024-09-01", before="2024-09-30")
    assert posts == []

def test_fetch_skips_malformed_posts():
    bad_post = {"id": "xyz"}  # missing required fields
    with patch("twi.ingestion.fetcher.search_posts", return_value=[bad_post]):
        posts = fetch_subreddit_posts("Teachers", after="2024-09-01", before="2024-09-30")
    assert posts == []  # malformed post is skipped, no exception raised