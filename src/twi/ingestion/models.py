from datetime import datetime
from pydantic import BaseModel


class RedditPost(BaseModel):
    reddit_id: str
    subreddit: str
    title: str
    body: str
    author: str | None
    score: int
    num_comments: int
    created_utc: datetime
    permalink: str