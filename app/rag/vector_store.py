"""A tiny in-memory vector store. No external vector database is needed
for a prototype of this size - cosine similarity over a numpy array is
fast enough for a few thousand chunks and keeps the dependency list short.
"""

import numpy as np


class VectorStore:
    def __init__(self, chunks, vectors):
        self.chunks = chunks
        self.vectors = vectors
        norms = np.linalg.norm(vectors, axis=1, keepdims=True)
        norms[norms == 0] = 1e-8
        self.normalized = vectors / norms

    def search(self, query_vector, top_k=4, filter_fn=None):
        candidate_indices = list(range(len(self.chunks)))
        if filter_fn is not None:
            candidate_indices = [i for i in candidate_indices if filter_fn(self.chunks[i])]
        if not candidate_indices:
            return []

        q_norm = query_vector / (np.linalg.norm(query_vector) + 1e-8)
        scores = self.normalized[candidate_indices] @ q_norm

        ranked = sorted(zip(candidate_indices, scores), key=lambda x: x[1], reverse=True)
        results = []
        for idx, score in ranked[:top_k]:
            results.append({"chunk": self.chunks[idx], "score": float(score)})
        return results
