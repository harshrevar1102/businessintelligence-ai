"""Ties ingestion, embeddings and the vector store together into a single
retrieval call, and applies entitlement filtering before anything is
handed to the LLM.
"""

import streamlit as st

from app.config.settings import RAG_TOP_K
from app.entitlement.entitlement import get_entitlement
from app.rag.embeddings import EmbeddingIndex
from app.rag.ingest import build_corpus
from app.rag.vector_store import VectorStore

POSITIVE_TOPIC_WORDS = {"normal", "usual", "quick", "great", "friendly", "loved"}
NEGATIVE_TOPIC_WORDS = {"long", "wait", "slow", "queue", "understaffed", "out", "unavailable"}


@st.cache_resource(show_spinner=False)
def build_index(_documents_df, _feedback_df):
    chunks = build_corpus(_documents_df, _feedback_df)
    texts = [c["text"] for c in chunks]
    index = EmbeddingIndex(texts)
    store = VectorStore(chunks, index.vectors)
    return store, index


def _entitlement_filter(persona, location_city, location_store):
    entitlement = get_entitlement(persona)

    def _filter(chunk):
        if entitlement["cities"] is not None and chunk["city"] not in entitlement["cities"] and chunk["city"] != "All":
            return False
        if entitlement["store"] is not None and chunk["store"] not in (entitlement["store"], "All"):
            return False
        if location_city and chunk["city"] not in (location_city, "All"):
            return False
        if location_store and chunk["store"] not in (location_store, "All"):
            return False
        return True

    return _filter


def retrieve_evidence(documents_df, feedback_df, query, persona, location_city, location_store, top_k=RAG_TOP_K):
    store, index = build_index(documents_df, feedback_df)
    query_vector = index.embed_query(query)
    filter_fn = _entitlement_filter(persona, location_city, location_store)
    results = store.search(query_vector, top_k=top_k, filter_fn=filter_fn)
    return results, index.backend


def detect_contradiction(results):
    """Heuristic contradiction check: do the retrieved chunks contain both
    clearly negative (shortage/complaint) and clearly positive/neutral
    (normal traffic) framing about the same location?"""
    has_negative = False
    has_positive = False
    for r in results:
        text_lower = r["chunk"]["text"].lower()
        if any(w in text_lower for w in NEGATIVE_TOPIC_WORDS):
            has_negative = True
        if any(w in text_lower for w in POSITIVE_TOPIC_WORDS):
            has_positive = True
    return has_negative and has_positive
