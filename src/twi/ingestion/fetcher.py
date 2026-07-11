from datetime import datetime, timezone
from twi.ingestion.arctic_client import search_posts
from twi.ingestion.models import RedditPost
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


def fetch_subreddit_posts(
    subreddit: str,
    after: str,
    before: str,
    limit: int = 500,
) -> list[RedditPost]:
    all_posts: list[RedditPost] = []
    current_after = after

    while len(all_posts) < limit:
        batch_size = min(100, limit - len(all_posts))
        raw_items = search_posts(subreddit, current_after, before, limit=batch_size)

        if not raw_items:
            break

        for raw in raw_items:
            post = _raw_to_post(raw, subreddit)
            if post:
                all_posts.append(post)

        last_ts = raw_items[-1]["created_utc"]
        last_dt = datetime.fromtimestamp(int(last_ts), tz=timezone.utc)
        current_after = last_dt.strftime("%Y-%m-%d")

        if len(raw_items) < 100:
            break

    log.info("Fetched %d posts from r/%s (%s to %s)", len(all_posts), subreddit, after, before)
    return all_posts