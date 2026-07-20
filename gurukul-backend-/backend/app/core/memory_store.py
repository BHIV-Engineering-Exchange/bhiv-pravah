
from typing import Dict, List
import logging

logger = logging.getLogger(__name__)

# Conversation Memory Storage
# Structure: {conversation_id: {"messages": [...], "created_at": "...", "updated_at": "..."}}
conversation_store: Dict[str, Dict] = {}

# RAG Knowledge Store (DEPRECATED - Now using VectorStoreService)
# Kept for backward compatibility, but new code should use VectorStoreService
# Structure: {hash: {"text": "...", "metadata": {...}}}
rag_knowledge_store: Dict[str, Dict] = {}

# Note: The vector store service is now the primary storage for RAG knowledge.
# See: backend/app/services/vector_store.py
# The in-memory dict above is kept for backward compatibility only.

# Saved Summaries Store
# Structure: {summary_id: {"title": "...", "content": "...", "source": "...", "created_at": "...", "questions": [...]}}
saved_summaries_store: Dict[str, Dict] = {}
# Compatibility for list-based usage in some endpoints
saved_summaries_db = []

# Questions Store
# Structure: {question_id: {"summary_id": "...", "type": "...", "question": "...", "answer": "...", "options": [...], "review_schedule": {...}}}
questions_store: Dict[str, Dict] = {}

# Quiz Store
# Structure: {quiz_id: {"subject": "...", "topic": "...", "questions": [...], "created_at": "...", "provider": "..."}}
quiz_store: Dict[str, Dict] = {}

# Helper stores for specific features
financial_profiles_store: Dict[str, Dict] = {}
wellness_profiles_store: Dict[str, Dict] = {}

# Flashcards DB (List based)
flashcards_db = []
