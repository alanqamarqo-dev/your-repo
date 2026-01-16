import os
import json
import math
import pathlib
from typing import List, Dict, Any, Optional

ARTIFACTS_DIR = pathlib.Path(os.getenv("AGL_ARTIFACTS_DIR", "artifacts"))
RAG_INDEX_PATH = ARTIFACTS_DIR / "rag_index.jsonl"

FAST_MODE = os.getenv("AGL_FAST_MODE", "0") == "1"


def _ensure_artifacts_dir():
    ARTIFACTS_DIR.mkdir(parents=True, exist_ok=True)


# ---------------------------------------------------------
# Embedding function (real → placeholder)
# ---------------------------------------------------------
def embed_text(text: str) -> List[float]:
    """
    في الوضع الحقيقي: نستخدم نموذج embeddings.
    في FAST_MODE: نستخدم length-based embedding.
    """
    if FAST_MODE:
        return [float(len(text)), float(len(text) % 13), float(len(text) % 7)]

    # Placeholder for real embedding
    return [float(len(text)), float(len(text) % 17), float(len(text) % 9)]


# ---------------------------------------------------------
# Cosine similarity
# ---------------------------------------------------------
def cosine(a: List[float], b: List[float]) -> float:
    dot = sum(x * y for x, y in zip(a, b))
    na = math.sqrt(sum(x * x for x in a))
    nb = math.sqrt(sum(y * y for y in b))
    if na == 0 or nb == 0:
        return 0.0
    return dot / (na * nb)


# ---------------------------------------------------------
# Add document
# ---------------------------------------------------------
def add_document(doc_id: str, text: str) -> None:
    _ensure_artifacts_dir()
    emb = embed_text(text)
    row = {
        "doc_id": doc_id,
        "text": text,
        "embedding": emb
    }
    with open(RAG_INDEX_PATH, "a", encoding="utf-8") as f:
        f.write(json.dumps(row, ensure_ascii=False) + "\n")


# ---------------------------------------------------------
# Load all documents
# ---------------------------------------------------------
def load_documents() -> List[Dict[str, Any]]:
    if not RAG_INDEX_PATH.exists():
        return []
    out = []
    for line in RAG_INDEX_PATH.read_text(encoding="utf-8").splitlines():
        try:
            out.append(json.loads(line))
        except Exception:
            pass
    return out


# ---------------------------------------------------------
# Search top-k
# ---------------------------------------------------------
def search(query: str, k: int = 5) -> List[Dict[str, Any]]:
    docs = load_documents()
    if not docs:
        return []

    q_emb = embed_text(query)

    scored = []
    for d in docs:
        sim = cosine(q_emb, d.get("embedding", []))
        scored.append((sim, d))

    scored.sort(key=lambda x: x[0], reverse=True)
    return [d for sim, d in scored[:k]]


# ---------------------------------------------------------
# Utility: prepare RAG context text
# ---------------------------------------------------------
def as_context(docs: List[Dict[str, Any]]) -> str:
    if not docs:
        return ""
    lines = ["[مقتطفات من ذاكرة RAG]:"]
    for d in docs:
        lines.append(f"- {d['text']}")
    return "\n".join(lines)


# ---------------------------------------------------------
# Main RAG retrieval
# ---------------------------------------------------------
def retrieve_context(query: str, k: int = 5) -> str:
    docs = search(query, k=k)
    return as_context(docs)
