"""Embedding backend with an Ollama-first, TF-IDF-fallback strategy.

If a local Ollama server with an embedding model is reachable, we use it
so the whole pipeline runs on local models end to end. If it isn't
reachable (Ollama not installed, model not pulled, etc.), the app
degrades gracefully to a scikit-learn TF-IDF vectorizer so retrieval
still works, it's just less semantically aware.
"""

import numpy as np
import requests
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings


def _ollama_embed(text):
    resp = requests.post(
        f"{settings.OLLAMA_HOST}/api/embeddings",
        json={"model": settings.OLLAMA_EMBED_MODEL, "prompt": text},
        timeout=settings.OLLAMA_REQUEST_TIMEOUT_SECONDS,
    )
    resp.raise_for_status()
    data = resp.json()
    return np.array(data["embedding"], dtype=np.float32)


def is_ollama_embedding_available():
    try:
        _ollama_embed("connection check")
        return True
    except Exception:
        return False


class EmbeddingIndex:
    """Holds the fitted embedding state for a corpus (either Ollama vectors
    or a fitted TF-IDF vectorizer) so queries can be embedded consistently."""

    def __init__(self, texts):
        self.texts = texts
        self.backend = "ollama"
        self.vectorizer = None
        self.vectors = None
        self._build(texts)

    def _build(self, texts):
        if is_ollama_embedding_available():
            try:
                vecs = [_ollama_embed(t) for t in texts]
                self.vectors = np.vstack(vecs)
                self.backend = "ollama"
                return
            except Exception:
                pass

        self.backend = "tfidf"
        self.vectorizer = TfidfVectorizer(max_features=2000, stop_words="english")
        self.vectors = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)

    def embed_query(self, query):
        if self.backend == "ollama":
            try:
                return _ollama_embed(query)
            except Exception:
                pass
        return self.vectorizer.transform([query]).toarray().astype(np.float32)[0]
