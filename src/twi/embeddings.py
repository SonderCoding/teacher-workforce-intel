import json
from functools import lru_cache
from pathlib import Path
import numpy as np
from sentence_transformers import SentenceTransformer

MODEL_NAME = "all-MiniLM-L6-v2"
EMB_DIR = Path("data/embeddings")
EMB_DIR.mkdir(parents=True, exist_ok=True)


@lru_cache(maxsize=1)
def get_model() -> SentenceTransformer:
    return SentenceTransformer(MODEL_NAME)


def encode_texts(texts: list[str], batch_size: int = 64) -> np.ndarray:
    return get_model().encode(
        texts,
        batch_size=batch_size,
        show_progress_bar=True,
        convert_to_numpy=True,
        normalize_embeddings=True,
    )


def save_embeddings(post_ids: list[int], embeddings: np.ndarray, name: str = "posts") -> None:
    np.save(EMB_DIR / f"{name}.npy", embeddings)
    (EMB_DIR / f"{name}_ids.json").write_text(json.dumps(post_ids))


def load_embeddings(name: str = "posts") -> tuple[list[int], np.ndarray]:
    ids = json.loads((EMB_DIR / f"{name}_ids.json").read_text())
    return ids, np.load(EMB_DIR / f"{name}.npy")


def semantic_search(
    query: str,
    post_ids: list[int],
    embeddings: np.ndarray,
    top_k: int = 5,
) -> list[tuple[int, float]]:
    query_vec = encode_texts([query])[0]
    scores = embeddings @ query_vec  # cosine similarity - both sides are normalized
    top_idx = np.argsort(-scores)[:top_k]
    return [(post_ids[i], float(scores[i])) for i in top_idx]