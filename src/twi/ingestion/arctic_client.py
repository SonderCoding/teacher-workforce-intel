import time
import requests
from twi.logging_config import get_logger

log = get_logger(__name__)

BASE_URL = "https://arctic-shift.photon-reddit.com/api"


def _get(endpoint: str, params: dict, max_retries: int = 3) -> dict:
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)

        # Check rate limit headers before doing anything else
        remaining = int(response.headers.get("X-RateLimit-Remaining", 10))
        if remaining < 3:
            reset_in = float(response.headers.get("X-RateLimit-Reset", 5))
            log.info("Rate limit low (%d remaining), sleeping %.1fs", remaining, reset_in)
            time.sleep(reset_in)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            wait = 2 ** attempt * 5  # exponential backoff: 5s, 10s, 20s
            log.warning("429 rate limited, retrying in %ds (attempt %d)", wait, attempt + 1)
            time.sleep(wait)
            continue

        if response.status_code >= 500:
            wait = 2 ** attempt * 3
            log.warning("Server error %d, retrying in %ds", response.status_code, wait)
            time.sleep(wait)
            continue

        response.raise_for_status()

    raise RuntimeError(f"Arctic Shift request failed after {max_retries} retries: {url}")


def search_posts(
    subreddit: str,
    after: str,
    before: str,
    limit: int = 100,
    sort: str = "asc",
) -> list[dict]:
    """
    Returns raw dicts from the Arctic Shift API.
    'after' and 'before' are ISO date strings, e.g. "2024-01-01".
    'limit' is capped at 100 per request by the API.
    """
    params = {
        "subreddit": subreddit,
        "after": after,
        "before": before,
        "limit": min(limit, 100),
        "sort": sort,
        "sort_type": "created_utc",
    }
    data = _get("/posts/search", params)
    return data.get("data", [])


def search_comments(
    subreddit: str,
    after: str,
    before: str,
    limit: int = 100,
) -> list[dict]:
    params = {
        "subreddit": subreddit,
        "after": after,
        "before": before,
        "limit": min(limit, 100),
    }
    data = _get("/comments/search", params)
    return data.get("data", [])