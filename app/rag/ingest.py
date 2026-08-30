"""Turns documents and feedback rows into a flat list of retrievable chunks.

Longer documents (emails, ops reports) get split into overlapping
word-chunks; feedback items are short enough to use as-is. Every chunk
keeps its source metadata so the retriever can filter by entitlement
before it ever reaches the LLM.
"""

from app.config.settings import RAG_CHUNK_SIZE_WORDS, RAG_CHUNK_OVERLAP_WORDS


def _chunk_text(text, size=RAG_CHUNK_SIZE_WORDS, overlap=RAG_CHUNK_OVERLAP_WORDS):
    words = text.split()
    if len(words) <= size:
        return [text]
    chunks = []
    start = 0
    while start < len(words):
        end = start + size
        chunks.append(" ".join(words[start:end]))
        start += size - overlap
    return chunks


def build_corpus(documents_df, feedback_df):
    chunks = []

    for _, doc in documents_df.iterrows():
        text_chunks = _chunk_text(doc["content"])
        for i, chunk_text in enumerate(text_chunks):
            chunks.append({
                "chunk_id": f"{doc['document_id']}-{i}",
                "text": chunk_text,
                "source_id": doc["document_id"],
                "source_type": doc["source_type"],
                "date": doc["date"],
                "city": doc["city"],
                "store": doc["store"],
                "subject": doc["subject"],
                "sensitivity": doc.get("sensitivity", "internal"),
            })

    for _, fb in feedback_df.iterrows():
        chunks.append({
            "chunk_id": fb["feedback_id"],
            "text": fb["text"],
            "source_id": fb["feedback_id"],
            "source_type": "customer_feedback",
            "date": fb["date"],
            "city": fb["city"],
            "store": fb["store"],
            "subject": f"Customer feedback ({fb['topic']}, rating {fb['rating']})",
            "sensitivity": "internal",
        })

    return chunks
