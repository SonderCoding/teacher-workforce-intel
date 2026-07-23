import json
import random
from pathlib import Path

import numpy as np

from twi.embeddings import load_embeddings
from twi.topics import fit_topics
from twi.logging_config import get_logger

logger = get_logger(__name__)

SAMPLE_PER_YEAR = 6000
MIN_CLUSTER_SIZE = 50
OUT_DIR = Path("data/topics")


def main():
    logger.info("Loading cached text")
    keyword_texts = json.loads((OUT_DIR / "keyword_texts.json").read_text(encoding="utf-8"))
    keyword_texts = {int(k): v for k, v in keyword_texts.items()}
    posts_by_year = json.loads((OUT_DIR / "posts_by_year.json").read_text(encoding="utf-8"))
    posts_by_year = {int(k): v for k, v in posts_by_year.items()}

    logger.info("Loading embeddings")
    ids, embeddings = load_embeddings()
    id_to_idx = {pid: i for i, pid in enumerate(ids)}

    nan_mask = np.isnan(embeddings).any(axis=1)
    bad_ids = set(ids[i] for i in range(len(ids)) if nan_mask[i])
    if bad_ids:
        logger.info(f"Excluding {len(bad_ids)} posts with NaN embeddings")
        with open(OUT_DIR / "excluded_nan_ids.json", "w") as f:
            json.dump(list(bad_ids), f)

    random.seed(42)
    sample_ids = []
    for year, year_ids in sorted(posts_by_year.items()):
        valid_ids = [pid for pid in year_ids if pid not in bad_ids and pid in keyword_texts]
        take = min(SAMPLE_PER_YEAR, len(valid_ids))
        sample_ids.extend(random.sample(valid_ids, take))
    logger.info(f"Sampled {len(sample_ids)} posts for fitting, stratified across {len(posts_by_year)} years")

    sample_texts = [keyword_texts[pid] for pid in sample_ids]
    sample_embeddings = embeddings[[id_to_idx[pid] for pid in sample_ids]]

    logger.info("Fitting BERTopic on sample")
    topic_model, sample_topic_ids = fit_topics(sample_texts, sample_embeddings, min_cluster_size=MIN_CLUSTER_SIZE)

    logger.info("Saving model immediately after fit")
    topic_model.save("data/bertopic_model", serialization="safetensors")

    assignments = dict(zip(sample_ids, [int(t) for t in sample_topic_ids]))
    with open(OUT_DIR / "sample_assignments.json", "w") as f:
        json.dump(assignments, f)

    topic_info = topic_model.get_topic_info()
    print("\n=== Topic Summary (from sample fit) ===")
    print(topic_info.to_string())
    logger.info("Done fitting. Model and sample assignments saved. Now run scripts/transform_topics.py")


if __name__ == "__main__":
    main()