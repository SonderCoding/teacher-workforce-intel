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
    consecutive_errors = 0

    while len(all_posts) < limit:
        batch_size = min(100, limit - len(all_posts))
        try:
            raw_items = search_posts(subreddit, current_after, before, limit=batch_size)
            consecutive_errors = 0
        except Exception as exc:
            consecutive_errors += 1
            if consecutive_errors >= 3:
                log.error("3 consecutive failures at %s, stopping: %s", current_after, exc)
                break
            log.warning("Request failed, retrying in 10s: %s", exc)
            import time
            time.sleep(10)
            continue

        if not raw_items:
            break

        for raw in raw_items:
            post = _raw_to_post(raw, subreddit)
            if post:
                all_posts.append(post)

        current_after = int(raw_items[-1]["created_utc"]) + 1

        if len(raw_items) < 100:
            break

    log.info("Fetched %d posts from r/%s (%s to %s)", len(all_posts), subreddit, after, before)
    return all_posts