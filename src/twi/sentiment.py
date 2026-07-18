from functools import lru_cache
from transformers import pipeline as hf_pipeline

TRANSFORMER_MODEL = "cardiffnlp/twitter-roberta-base-sentiment-latest"
LABEL_MAP = {"negative": -1, "neutral": 0, "positive": 1}


@lru_cache(maxsize=1)
def _get_pipeline():
    return hf_pipeline(
        "sentiment-analysis",
        model=TRANSFORMER_MODEL,
        truncation=True,
        device=0,
    )


def transformer_score_batch(texts: list[str]) -> list[float]:
    results = _get_pipeline()([t[:512] for t in texts], batch_size=128)
    return [LABEL_MAP[r["label"]] * r["score"] for r in results]