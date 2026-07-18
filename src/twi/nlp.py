import re
from functools import lru_cache
import spacy

URL_RE = re.compile(r"https?://\S+")
MD_RE = re.compile(r"[*_~`]")
REF_RE = re.compile(r"/u/\w+|/r/\w+")


@lru_cache(maxsize=1)
def get_nlp():
    return spacy.load("en_core_web_sm")


def _strip_markdown(text: str) -> str:
    text = URL_RE.sub(" ", text)
    text = REF_RE.sub(" ", text)
    text = MD_RE.sub("", text)
    return re.sub(r"\s+", " ", text).strip()


def clean_for_embedding(text: str) -> str:
    """Light cleaning - used in sentiment analysis"""
    return _strip_markdown(text)


def clean_for_keywords(text: str) -> str:
    """Cleaning for theme detections"""
    doc = get_nlp()(_strip_markdown(text))
    tokens = [
        t.lemma_.lower()
        for t in doc
        if not t.is_stop and not t.is_punct and not t.is_space and t.is_alpha
    ]
    return " ".join(tokens)


