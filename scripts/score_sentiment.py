import random
from datetime import datetime, timezone
from twi.db.base import SessionLocal
from twi.db.models import Post, SentimentScore
from twi.nlp import clean_for_embedding
from twi.sentiment import transformer_score_batch
from twi.logging_config import configure_logging, get_logger

configure_logging()
log = get_logger(__name__)

POSTS_PER_YEAR = 999999
BATCH_SIZE = 128
YEARS = list(range(2016, 2027))


def is_usable(post) -> bool:
    if post.body in ("[deleted]", "[removed]"):
        return False
    if post.author == "[deleted]" and not post.body:
        return False
    combined = f"{post.title} {post.body}".strip()
    if len(combined) < 20:
        return False
    return True


def already_scored(session, post_id: int) -> bool:
    return session.query(SentimentScore).filter_by(post_id=post_id).first() is not None


def run():
    session = SessionLocal()
    try:
        for year in YEARS:
            log.info("Starting year %d", year)

            year_start = datetime(year, 1, 1, tzinfo=timezone.utc)
            year_end = datetime(year + 1, 1, 1, tzinfo=timezone.utc)

            all_posts = (
                session.query(Post)
                .filter(Post.created_utc >= year_start)
                .filter(Post.created_utc < year_end)
                .all()
            )

            usable = [p for p in all_posts if is_usable(p)]
            unscored = [p for p in usable if not already_scored(session, p.id)]

            if not unscored:
                log.info("Year %d already fully scored, skipping", year)
                continue

            sample = random.sample(unscored, min(POSTS_PER_YEAR, len(unscored)))
            log.info("Year %d: %d usable posts available, scoring %d", year, len(usable), len(sample))

            for i in range(0, len(sample), BATCH_SIZE):
                batch = sample[i:i + BATCH_SIZE]
                texts = [clean_for_embedding(f"{p.title}. {p.body}") for p in batch]
                scores = transformer_score_batch(texts)

                for post, score in zip(batch, scores):
                    existing = session.query(SentimentScore).filter_by(post_id=post.id).one_or_none()
                    if existing:
                        existing.transformer_score = score
                    else:
                        session.add(SentimentScore(
                            post_id=post.id,
                            transformer_score=score,
                        ))

                session.commit()
                log.info("Year %d: scored batch %d/%d", year, min(i + BATCH_SIZE, len(sample)), len(sample))

        log.info("Sentiment scoring complete")
    finally:
        session.close()


if __name__ == "__main__":
    run()