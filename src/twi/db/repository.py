from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.orm import Session
from twi.db.models import Post, Subreddit
from twi.ingestion.models import RedditPost


def get_or_create_subreddit(session: Session, name: str) -> Subreddit:
    sub = session.query(Subreddit).filter_by(name=name).one_or_none()
    if sub is None:
        sub = Subreddit(name=name)
        session.add(sub)
        session.flush()
    return sub


def upsert_posts(session: Session, posts: list[RedditPost]) -> int:
    if not posts:
        return 0
    sub_cache: dict[str, int] = {}
    rows = []
    for p in posts:
        if p.subreddit not in sub_cache:
            sub_cache[p.subreddit] = get_or_create_subreddit(session, p.subreddit).id
        rows.append({
            "reddit_id": p.reddit_id,
            "subreddit_id": sub_cache[p.subreddit],
            "title": p.title,
            "body": p.body,
            "author": p.author,
            "score": p.score,
            "num_comments": p.num_comments,
            "created_utc": p.created_utc,
        })
    stmt = pg_insert(Post).values(rows)
    stmt = stmt.on_conflict_do_update(
        index_elements=["reddit_id"],
        set_={
            "score": stmt.excluded.score,
            "num_comments": stmt.excluded.num_comments,
        },
    )
    session.execute(stmt)
    session.commit()
    return len(rows)