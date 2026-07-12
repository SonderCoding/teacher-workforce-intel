import time
from datetime import datetime, timezone
import requests
from twi.logging_config import get_logger

log = get_logger(__name__)

BASE_URL = "https://arctic-shift.photon-reddit.com/api"


def _get(endpoint: str, params: dict, max_retries: int = 3) -> dict:
    url = f"{BASE_URL}{endpoint}"
    for attempt in range(max_retries):
        response = requests.get(url, params=params, timeout=30)

        remaining = int(response.headers.get("X-RateLimit-Remaining", 10))
        if remaining < 3:
            reset_in = float(response.headers.get("X-RateLimit-Reset", 5))
            log.info("Rate limit low (%d remaining), sleeping %.1fs", remaining, reset_in)
            time.sleep(reset_in)

        if response.status_code == 200:
            return response.json()

        if response.status_code == 429:
            wait = 2 ** attempt * 5
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


def _to_timestamp(value) -> int:
    if isinstance(value, int):
        return value
    return int(datetime.strptime(value, "%Y-%m-%d").replace(tzinfo=timezone.utc).timestamp())


def search_posts(
    subreddit: str,
    after,
    before: str,
    limit: int = 100,
    sort: str = "asc",
) -> list[dict]:
    params = {
        "subreddit": subreddit,
        "after": _to_timestamp(after),
        "before": _to_timestamp(before),
        "limit": min(limit, 100),
        "sort": sort,
        "sort_type": "created_utc",
    }
    return _get("/posts/search", params).get("data", [])