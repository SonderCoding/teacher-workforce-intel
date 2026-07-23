from bertopic import BERTopic
from umap import UMAP
from hdbscan import HDBSCAN
from sklearn.feature_extraction.text import CountVectorizer
import numpy as np


def build_topic_model(min_cluster_size: int = 50) -> BERTopic:
    umap_model = UMAP(
        n_neighbors=15,
        n_components=5,
        min_dist=0.0,
        metric="cosine",
        random_state=42,
    )
    hdbscan_model = HDBSCAN(
        min_cluster_size=min_cluster_size,
        metric="euclidean",
        cluster_selection_method="eom",
        prediction_data=True,
    )
    vectorizer_model = CountVectorizer(stop_words="english", ngram_range=(1, 2))
    return BERTopic(
        umap_model=umap_model,
        hdbscan_model=hdbscan_model,
        vectorizer_model=vectorizer_model,
        calculate_probabilities=False,
        verbose=True,
    )


def fit_topics(texts: list[str], embeddings: np.ndarray, min_cluster_size: int = 50):
    model = build_topic_model(min_cluster_size)
    topic_ids, _ = model.fit_transform(texts, embeddings=embeddings)
    return model, topic_ids


def _transform_chunk(model: BERTopic, ids_chunk, texts_chunk, embeddings_chunk, poisoned_ids: list):
    try:
        topic_ids, _ = model.transform(texts_chunk, embeddings=embeddings_chunk)
        return dict(zip(ids_chunk, [int(t) for t in topic_ids]))
    except ValueError as e:
        if "NaN" not in str(e) and "infinity" not in str(e):
            raise
        if len(ids_chunk) == 1:
            poisoned_ids.append(ids_chunk[0])
            return {ids_chunk[0]: -1}
        mid = len(ids_chunk) // 2
        left = _transform_chunk(model, ids_chunk[:mid], texts_chunk[:mid], embeddings_chunk[:mid], poisoned_ids)
        right = _transform_chunk(model, ids_chunk[mid:], texts_chunk[mid:], embeddings_chunk[mid:], poisoned_ids)
        left.update(right)
        return left


def transform_in_batches(model: BERTopic, ids: list, texts: list[str], embeddings: np.ndarray, batch_size: int = 20000):
    assignments = {}
    poisoned_ids = []
    total = len(texts)
    for start in range(0, total, batch_size):
        end = min(start + batch_size, total)
        chunk_result = _transform_chunk(
            model,
            ids[start:end],
            texts[start:end],
            embeddings[start:end],
            poisoned_ids,
        )
        assignments.update(chunk_result)
        print(f"Transformed {end}/{total} posts ({len(poisoned_ids)} poisoned so far)")
    return assignments, poisoned_ids