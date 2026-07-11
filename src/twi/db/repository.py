import psycopg2
from sqlalchemy.orm import Session
from twi.db.base import engine
from twi.db.models import Subreddit
from twi.ingestion.models import RedditPost


def get_or_create_subreddit(session: Session, name: str) -> int:
    sub = session.query(Subreddit).filter_by(name=name).one_or_none()
    if sub is None:
        sub = Subreddit(name=name)
        session.add(sub)
        session.commit()
    return sub.id


def upsert_posts(session: Session, posts: list[RedditPost]) -> int:
    if not posts:
        return 0

    subreddit_id = get_or_create_subreddit(session, posts[0].subreddit)

    rows = [(
        p.reddit_id,
        subreddit_id,
        p.title,
        p.body,
        p.author,
        p.score,
        p.num_comments,
        p.created_utc,
    ) for p in posts]

    with engine.connect() as conn:
        raw = conn.connection
        with raw.cursor() as cur:
            for i in range(0, len(rows), 500):
                batch = rows[i:i + 500]
                cur.executemany("""
                    INSERT INTO posts (reddit_id, subreddit_id, title, body, author, score, num_comments, created_utc)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (reddit_id)
                    DO UPDATE SET score = EXCLUDED.score, num_comments = EXCLUDED.num_comments
                """, batch)
            raw.commit()

    return len(rows)