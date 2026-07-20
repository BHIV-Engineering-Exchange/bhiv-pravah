import sqlite3
import os
import json
import logging
from typing import Any, Dict, List

logger = logging.getLogger("uniguru.rag.engine")

MIN_SIMILARITY_THRESHOLD = float(os.getenv("UNIGURU_RAG_CONFIDENCE_MIN", "0.78"))
TOP_K = int(os.getenv("UNIGURU_RAG_TOP_K", "5"))

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "chunks.db")
faiss_path = os.path.join(base_dir, "faiss_index.bin")

engine = None

def _normalize_chunk_text(text: str) -> str:
    return " ".join(str(text or "").split()).strip()


def _log_rag_debug(query: str, candidates: List[Dict[str, Any]], selected: List[Dict[str, Any]], rejected: List[Dict[str, Any]], final_context: str) -> None:
    debug_payload = {
        "stage": "rag_debug",
        "query": query,
        "threshold": MIN_SIMILARITY_THRESHOLD,
        "retrieved_documents": [
            {
                "id": candidate.get("id"),
                "score": candidate.get("score"),
                "file_name": candidate.get("metadata", {}).get("file_name"),
            }
            for candidate in candidates
        ],
        "selected_chunks": [
            {
                "id": chunk.get("id"),
                "score": chunk.get("score"),
                "file_name": chunk.get("metadata", {}).get("file_name"),
            }
            for chunk in selected
        ],
        "rejected_chunks": rejected,
        "final_context_snippet": final_context[:1000],
        "selected_count": len(selected),
        "rejected_count": len(rejected),
    }
    logger.info(json.dumps(debug_payload, default=str, sort_keys=True))


def _index_available() -> bool:
    return os.path.exists(faiss_path) and os.path.exists(db_path)


class NewRAGEngine:
    def __init__(self, model_name=None):
        if not _index_available():
            raise FileNotFoundError(
                f"FAISS index missing. Expected {faiss_path} and {db_path}. "
                "Run index build or mount persistent storage on Render."
            )

        import faiss
        import numpy as np
        from sentence_transformers import SentenceTransformer

        model_name = model_name or os.getenv("UNIGURU_EMBEDDING_MODEL", "all-MiniLM-L6-v2")
        self.model = SentenceTransformer(model_name)
        self.index = faiss.read_index(faiss_path)
        self.db_path = db_path
        self._faiss = faiss
        self.ollama = self._init_ollama()

    def _init_ollama(self):
        try:
            from integrations.ollama_client import OllamaClient
            return OllamaClient()
        except Exception:
            return None

    def retrieve(self, query: str, top_k: int = 5):
        query_emb = self.model.encode([query])
        self._faiss.normalize_L2(query_emb)
        scores, ids = self.index.search(query_emb, top_k)

        candidates: List[Dict[str, Any]] = []
        with sqlite3.connect(self.db_path) as conn:
            cur = conn.cursor()
            for score, doc_id in zip(scores[0], ids[0]):
                if doc_id == -1:
                    continue
                cur.execute(
                    "SELECT file_name, page_number, text FROM chunks WHERE id = ?",
                    (int(doc_id),),
                )
                row = cur.fetchone()
                if not row:
                    continue
                candidates.append(
                    {
                        "id": int(doc_id),
                        "text": row[2],
                        "metadata": {"file_name": row[0], "page_number": row[1]},
                        "score": float(score),
                    }
                )

        candidates.sort(key=lambda candidate: candidate["score"], reverse=True)

        selected: List[Dict[str, Any]] = []
        rejected: List[Dict[str, Any]] = []
        seen_texts = set()

        for candidate in candidates:
            score = candidate["score"]
            normalized_text = _normalize_chunk_text(candidate["text"])

            if score < MIN_SIMILARITY_THRESHOLD:
                rejected.append(
                    {
                        "id": candidate["id"],
                        "score": score,
                        "reason": "below_threshold",
                        "file_name": candidate["metadata"].get("file_name"),
                    }
                )
                continue

            if normalized_text in seen_texts:
                rejected.append(
                    {
                        "id": candidate["id"],
                        "score": score,
                        "reason": "duplicate_chunk",
                        "file_name": candidate["metadata"].get("file_name"),
                    }
                )
                continue

            seen_texts.add(normalized_text)
            selected.append(candidate)
            if len(selected) >= TOP_K:
                break

        final_context = "\n\n".join(
            f"--- [{idx + 1}] {chunk['metadata']['file_name']} (page {chunk['metadata'].get('page_number', '?')}) ---\n{chunk['text']}"
            for idx, chunk in enumerate(selected)
        )
        if len(final_context) > 5000:
            final_context = final_context[:5000] + "\n...[truncated]"

        _log_rag_debug(query, candidates, selected, rejected, final_context)
        return selected

    def _synthesize_with_ollama(self, query: str, context: str) -> str:
        if not self.ollama or not self.ollama.enabled:
            return ""
        system_prompt = (
            "You are UniGuru, a sovereign knowledge assistant. "
            "Answer ONLY using the provided context. If context is insufficient, reply exactly: "
            "'I do not have verified knowledge to answer this question.'"
        )
        user_prompt = f"Context:\n{context}\n\nQuestion: {query}\n\nAnswer:"
        return self.ollama.generate(user_prompt, system_prompt=system_prompt) or ""

    def answer_question(self, query: str, max_context_chars: int = 4000, top_k: int = 5):
        retrieved = self.retrieve(query, top_k=top_k)
        if not retrieved:
            return {"answer": "No relevant context found.", "retrieved": []}

        context_parts = []
        for i, chunk in enumerate(retrieved):
            meta = chunk["metadata"]
            context_parts.append(
                f"--- [{i + 1}] {meta['file_name']} (page {meta.get('page_number', '?')}) ---\n{chunk['text']}"
            )
        context = "\n\n".join(context_parts)
        if len(context) > max_context_chars:
            context = context[:max_context_chars] + "\n...[truncated]"

        answer = self._synthesize_with_ollama(query, context)
        if not answer:
            # No LLM generation or context was insufficient, return explicit no-knowledge answer.
            return {"answer": "No relevant context found.", "retrieved": retrieved}

        return {"answer": answer, "retrieved": retrieved}


def get_engine():
    global engine
    if engine is None:
        engine = NewRAGEngine()
    return engine


def get_index_status() -> dict:
    status = {
        "faiss_index_exists": os.path.exists(faiss_path),
        "chunks_db_exists": os.path.exists(db_path),
        "faiss_path": faiss_path,
        "db_path": db_path,
        "vector_count": 0,
        "chunk_count": 0,
    }
    if status["chunks_db_exists"]:
        try:
            with sqlite3.connect(db_path) as conn:
                cur = conn.cursor()
                cur.execute("SELECT COUNT(*) FROM chunks")
                status["chunk_count"] = int(cur.fetchone()[0])
        except Exception as exc:
            status["db_error"] = str(exc)
    if status["faiss_index_exists"]:
        try:
            import faiss
            index = faiss.read_index(faiss_path)
            status["vector_count"] = int(index.ntotal)
        except Exception as exc:
            status["faiss_error"] = str(exc)
    return status
