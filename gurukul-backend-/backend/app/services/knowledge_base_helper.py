"""
Knowledge Base Helper - Provides unified interface for vector store with fallback
Uses Embedding_LM libraries (sentence-transformers, chromadb) for semantic search
"""

from typing import Dict, Optional, List, Any
import logging

logger = logging.getLogger(__name__)

# Global vector store instance (lazy loaded)
_vector_store_instance = None

def get_vector_store():
    """Get or create vector store instance"""
    global _vector_store_instance
    if _vector_store_instance is None:
        try:
            from app.services.vector_store import VectorStoreService
            from app.core.config import settings
            
            _vector_store_instance = VectorStoreService(
                backend=settings.VECTOR_STORE_BACKEND,
                collection_name=settings.VECTOR_STORE_COLLECTION
            )
            logger.info(f"Vector store initialized: {settings.VECTOR_STORE_BACKEND}")
        except Exception as e:
            logger.error(f"Failed to initialize vector store: {e}")
            _vector_store_instance = None
    return _vector_store_instance

def get_knowledge_base_context(
    query: str,
    top_k: int = 3,
    filter_metadata: Optional[Dict[str, Any]] = None,
    use_knowledge_base: bool = True
) -> Dict[str, Any]:
    """
    Get context from knowledge base with fallback handling
    
    Args:
        query: Search query
        top_k: Number of results to retrieve
        filter_metadata: Optional metadata filters (e.g., {"subject": "Physics"})
        use_knowledge_base: Whether to attempt knowledge base retrieval
    
    Returns:
        Dict with:
        - context: Retrieved context string (empty if failed)
        - knowledge_base_used: Whether KB was successfully used
        - results: List of search results
        - error: Error message if failed (None if success)
    """
    result = {
        "context": "",
        "knowledge_base_used": False,
        "results": [],
        "error": None
    }
    
    if not use_knowledge_base:
        return result
    
    try:
        vector_store = get_vector_store()
        if not vector_store:
            result["error"] = "Vector store not available"
            logger.warning("Vector store not available, will use Groq only")
            return result
        
        # Search knowledge base
        search_results = vector_store.search(
            query=query,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        if search_results:
            # Format context from results
            context_parts = []
            for i, res in enumerate(search_results, 1):
                context_parts.append(
                    f"[Knowledge {i}] {res['text']}\n"
                    f"Source: {res['metadata'].get('source', 'Unknown')}"
                )
            
            result["context"] = "\n\n".join(context_parts)
            result["knowledge_base_used"] = True
            result["results"] = search_results
            
            logger.info(f"Knowledge base context retrieved: {len(result['context'])} characters, {len(search_results)} results")
        else:
            result["error"] = "No relevant content found in knowledge base"
            logger.info("No relevant content found in knowledge base, will use Groq only")
    
    except Exception as e:
        result["error"] = str(e)
        logger.warning(f"Knowledge base retrieval failed (non-fatal): {e}, will use Groq only")
    
    return result

def enhance_prompt_with_context(
    base_prompt: str,
    query: str,
    context: str,
    include_context_instruction: bool = True
) -> str:
    """
    Enhance a prompt with knowledge base context
    
    Args:
        base_prompt: Base prompt/instruction
        query: User query
        context: Retrieved context from knowledge base
        include_context_instruction: Whether to add instruction about using context
    
    Returns:
        Enhanced prompt with context
    """
    if not context:
        return f"{base_prompt}\n\n{query}"
    
    if include_context_instruction:
        enhanced = f"""{base_prompt}

Use the following knowledge base context to inform your response:
{context}

Now answer the user's question based on this context and your knowledge: {query}"""
    else:
        enhanced = f"""{base_prompt}

Context from knowledge base:
{context}

User query: {query}"""
    
    return enhanced
