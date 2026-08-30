"""Embedding backend with an OpenAI-first, TF-IDF-fallback strategy.

If the OpenAI API is reachable, we use it. If it isn't, the app degrades
gracefully to a scikit-learn TF-IDF vectorizer so retrieval still works.
"""

import numpy as np
from openai import OpenAI
from sklearn.feature_extraction.text import TfidfVectorizer

from app.config import settings


def _get_client():
    kwargs = {"api_key": settings.OPENAI_API_KEY}
    if settings.OPENAI_BASE_URL:
        kwargs["base_url"] = settings.OPENAI_BASE_URL
    return OpenAI(**kwargs)


def _openai_embed(text):
    client = _get_client()
    resp = client.embeddings.create(
        input=[text],
        model=settings.OPENAI_EMBED_MODEL,
        timeout=settings.OPENAI_REQUEST_TIMEOUT_SECONDS,
    )
    return np.array(resp.data[0].embedding, dtype=np.float32)


def is_openai_embedding_available():
    try:
        _openai_embed("connection check")
        return True
    except Exception:
        return False


class EmbeddingIndex:
    """Holds the fitted embedding state for a corpus (either OpenAI vectors
    or a fitted TF-IDF vectorizer) so queries can be embedded consistently."""

    def __init__(self, texts):
        self.texts = texts
        self.backend = "openai"
        self.vectorizer = None
        self.vectors = None
        self._build(texts)

    def _build(self, texts):
        if is_openai_embedding_available():
            try:
                # To be gentle on API limits, do them all in one call if possible
                client = _get_client()
                resp = client.embeddings.create(
                    input=texts,
                    model=settings.OPENAI_EMBED_MODEL,
                    timeout=settings.OPENAI_REQUEST_TIMEOUT_SECONDS,
                )
                self.vectors = np.array([item.embedding for item in resp.data], dtype=np.float32)
                self.backend = "openai"
                return
            except Exception:
                pass

        self.backend = "tfidf"
        self.vectorizer = TfidfVectorizer(max_features=2000, stop_words="english")
        self.vectors = self.vectorizer.fit_transform(texts).toarray().astype(np.float32)

    def embed_query(self, query):
        if self.backend == "openai":
            try:
                return _openai_embed(query)
            except Exception:
                pass
        return self.vectorizer.transform([query]).toarray().astype(np.float32)[0]

