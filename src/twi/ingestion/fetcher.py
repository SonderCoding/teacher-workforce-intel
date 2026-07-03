from datetime import datetime, timezone
from twi.ingestion.arctic_client import search_posts, search_comments
from twi.ingestion.models import RedditPost, RedditComment
from twi.logging_config import get_logger

log = get_logger(__name__)


def _parse_utc(value) -> datetime:
    return datetime.fromtimestamp(int(value), tz=timezone.utc)


def _raw_to_post(raw: dict, subreddit: str) -> RedditPost | None:
    try:
        return RedditPost(
            reddit_id=raw["id"],
            subreddit=subreddit,
            title=raw.get("title", ""),
            body=raw.get("selftext", "") or "",
            author=raw.get("author") or None,
            score=int(raw.get("score", 0)),
            num_comments=int(raw.get("num_comments", 0)),
            created_utc=_parse_utc(raw["created_utc"]),
            permalink=raw.get("permalink", ""),
        )
    except Exception as exc:
        log.warning("Skipping malformed post %s: %s", raw.get("id", "?"), exc)
        return None


def _raw_to_comment(raw: dict, subreddit: str) -> RedditComment | None:
    try:
        return RedditComment(
            reddit_id=raw["id"],
            post_reddit_id=raw.get("link_id", "").replace("t3_", ""),
            subreddit=subreddit,
            body=raw.get("body", "") or "",
            author=raw.get("author") or None,
            score=int(raw.get("score", 0)),
            created_utc=_parse_utc(raw["created_utc"]),
        )
    except Exception as exc:
        log.warning("Skipping malformed comment %s: %s", raw.get("id", "?"), exc)
        return None


def fetch_subreddit_posts(
    subreddit: str,
    after: str,
    before: str,
    limit: int = 500,
) -> list[RedditPost]:
    """
    Fetches up to `limit` posts from a subreddit within a date range.
    Pages through Arctic Shift results automatically (100 posts per request).
    'after' and 'before' are ISO date strings, e.g. "2024-01-01".
    """
    all_posts: list[RedditPost] = []
    current_after = after

    while len(all_posts) < limit:
        batch_size = min(100, limit - len(all_posts))
        raw_items = search_posts(subreddit, current_after, before, limit=batch_size)

        if not raw_items:
            break  # no more results in this date range

        for raw in raw_items:
            post = _raw_to_post(raw, subreddit)
            if post:
                all_posts.append(post)

        # Advance the window to just after the last post's timestamp
        last_ts = raw_items[-1]["created_utc"]
        current_after = str(int(last_ts) + 1)

        if len(raw_items) < 100:
            break  # last page, fewer results than requested

    log.info("Fetched %d posts from r/%s (%s to %s)", len(all_posts), subreddit, after, before)
    return all_posts


def fetch_subreddit_comments(
    subreddit: str,
    after: str,
    before: str,
    limit: int = 500,
) -> list[RedditComment]:
    """Same pagination logic as fetch_subreddit_posts, for comments."""
    all_comments: list[RedditComment] = []
    current_after = after

    while len(all_comments) < limit:
        batch_size = min(100, limit - len(all_comments))
        raw_items = search_comments(subreddit, current_after, before, limit=batch_size)

        if not raw_items:
            break

        for raw in raw_items:
            comment = _raw_to_comment(raw, subreddit)
            if comment:
                all_comments.append(comment)

        last_ts = raw_items[-1]["created_utc"]
        current_after = str(int(last_ts) + 1)

        if len(raw_items) < 100:
            break

    log.info("Fetched %d comments from r/%s", len(all_comments), subreddit)
    return all_comments