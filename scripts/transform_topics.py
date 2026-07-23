import json
from pathlib import Path

from bertopic import BERTopic

from twi.embeddings import load_embeddings
from twi.topics import transform_in_batches
from twi.logging_config import get_logger

logger = get_logger(__name__)

TRANSFORM_BATCH_SIZE = 20000
OUT_DIR = Path("data/topics")


def main():
    logger.info("Loading model and cached data")
    topic_model = BERTopic.load("data/bertopic_model")
    keyword_texts = json.loads((OUT_DIR / "keyword_texts.json").read_text(encoding="utf-8"))
    keyword_texts = {int(k): v for k, v in keyword_texts.items()}
    sample_assignments = json.loads((OUT_DIR / "sample_assignments.json").read_text(encoding="utf-8"))
    sample_assignments = {int(k): v for k, v in sample_assignments.items()}

    ids, embeddings = load_embeddings()
    id_to_idx = {pid: i for i, pid in enumerate(ids)}

    assignments = dict(sample_assignments)

    remaining_ids = [pid for pid in ids if pid not in assignments and pid in keyword_texts]
    logger.info(f"Transforming {len(remaining_ids)} remaining posts")

    remaining_texts = [keyword_texts[pid] for pid in remaining_ids]
    remaining_embeddings = embeddings[[id_to_idx[pid] for pid in remaining_ids]]

    remaining_assignments, poisoned_ids = transform_in_batches(
        topic_model, remaining_ids, remaining_texts, remaining_embeddings, batch_size=TRANSFORM_BATCH_SIZE
    )
    assignments.update(remaining_assignments)

    if poisoned_ids:
        logger.info(f"{len(poisoned_ids)} posts triggered NaN during transform, marked as noise")
        with open(OUT_DIR / "poisoned_ids.json", "w") as f:
            json.dump(poisoned_ids, f)

    with open(OUT_DIR / "assignments.json", "w") as f:
        json.dump(assignments, f)

    logger.info(f"Done. {len(assignments)} total posts assigned. Saved to data/topics/assignments.json")


if __name__ == "__main__":
    main()