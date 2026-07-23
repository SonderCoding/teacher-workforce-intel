import json
from pathlib import Path

from bertopic import BERTopic
from twi.db.base import SessionLocal
from twi.db.models import Post, Topic
from twi.logging_config import get_logger

logger = get_logger(__name__)

EXCLUDED_TOPIC_IDS = [
    0, 1, 5, 7, 8, 9, 10, 11, 13, 14, 15, 16, 17, 19, 20, 21, 23, 24, 25, 26,
    27, 28, 29, 31, 34, 35, 36, 38, 39, 40, 41, 42, 43, 45, 47, 48, 50, 51,
    52, 54, 55, 56, 57, 58, 61, 62, 63, 64, 65, 66, 67, 69, 70, 74, 75, 76,
    77, 78, 79, 80, 82, 83, 84, 85, 86, 89, 90, 91, 92, 94, 95, 96, 98, 99,
    100, 101, 103, 104, 105, 107, 108, 109
]


def main():
    logger.info("Loading saved model and assignments")
    topic_model = BERTopic.load("data/bertopic_model")
    assignments = json.loads(Path("data/topics/assignments.json").read_text())
    assignments = {int(k): v for k, v in assignments.items()}

    logger.info(f"Excluding topics: {EXCLUDED_TOPIC_IDS}")

    session = SessionLocal()
    logger.info("Clearing existing topic data")
    session.query(Post).update({Post.topic_id: None})
    session.query(Topic).delete()
    session.commit()

    topic_info = topic_model.get_topic_info()
    kept = 0
    for _, row in topic_info.iterrows():
        topic_id = int(row["Topic"])
        if topic_id == -1 or topic_id in EXCLUDED_TOPIC_IDS:
            continue
        keywords = [w for w, _ in topic_model.get_topic(topic_id)][:8]
        t = Topic(id=topic_id, label=row["Name"], keywords=", ".join(keywords))
        session.add(t)
        kept += 1
    session.commit()
    logger.info(f"Wrote {kept} topics")

    updated = 0
    batch = []
    for post_id, topic_id in assignments.items():
        final_topic_id = topic_id if topic_id != -1 and topic_id not in EXCLUDED_TOPIC_IDS else None
        batch.append((post_id, final_topic_id))
        if len(batch) >= 5000:
            session.bulk_update_mappings(Post, [{"id": pid, "topic_id": tid} for pid, tid in batch])
            session.commit()
            updated += len(batch)
            logger.info(f"Updated {updated} posts")
            batch = []
    if batch:
        session.bulk_update_mappings(Post, [{"id": pid, "topic_id": tid} for pid, tid in batch])
        session.commit()
        updated += len(batch)

    session.close()
    logger.info(f"Done. Updated {updated} posts total")


if __name__ == "__main__":
    main()