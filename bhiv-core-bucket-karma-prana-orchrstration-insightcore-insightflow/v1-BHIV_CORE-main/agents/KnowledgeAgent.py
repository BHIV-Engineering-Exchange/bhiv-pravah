from utils.file_based_retriever import file_retriever
from utils.logger import get_logger
import uuid
import os
from datetime import datetime
from reinforcement.rl_context import RLContext
from reinforcement.reward_functions import get_reward_from_output
from typing import Dict, Any

# Try to import VedabaseRetriever, but don't fail if not available
try:
    from vedabase_retriever import VedabaseRetriever
    QDRANT_AVAILABLE = True
except ImportError as e:
    logger = get_logger(__name__)
    logger.warning(f"VedabaseRetriever not available: {e}")
    VedabaseRetriever = None
    QDRANT_AVAILABLE = False

# Try to import NAS retriever for enhanced knowledge retrieval
try:
    # Import via package path first, fallback to relative example path
    from example.nas_retriever import NASKnowledgeRetriever
    NAS_RETRIEVER_AVAILABLE = True
except Exception as e:
    logger = get_logger(__name__)
    logger.warning(f"NAS retriever not available: {e}")
    NASKnowledgeRetriever = None
    NAS_RETRIEVER_AVAILABLE = False

logger = get_logger(__name__)

class KnowledgeAgent:
    """Agent for handling knowledge base queries with multi-folder vector search."""
    
    def __init__(self):
        """Initialize the KnowledgeAgent with multi-folder support."""
        self.name = "KnowledgeAgent"
        self.description = "Agent for comprehensive knowledge retrieval across all NAS folders"
        
        # Initialize multi-folder vector manager
        try:
            from multi_folder_vector_manager import MultiFolderVectorManager
            self.multi_folder_manager = MultiFolderVectorManager()
            self.multi_folder_available = True
            logger.info("✅ Multi-folder vector manager initialized successfully")
        except Exception as e:
            logger.warning(f"⚠️ Multi-folder manager not available: {e}")
            self.multi_folder_available = False
            self.multi_folder_manager = None
        
        # Initialize other retrievers as fallback
        self.initialize_fallback_retrievers()
    
    def initialize_fallback_retrievers(self):
        """Initialize fallback retrievers if multi-folder manager is not available."""
        # Try NAS+Qdrant retriever
        try:
            from example.nas_retriever import NASKnowledgeRetriever
            self.nas_retriever = NASKnowledgeRetriever("vedas", qdrant_url="localhost:6333")
            self.nas_available = self.nas_retriever.qdrant_available
            if self.nas_available:
                logger.info("✅ NAS retriever initialized as fallback")
            else:
                logger.warning("⚠️ NAS retriever not available")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize NAS retriever: {e}")
            self.nas_available = False
            self.nas_retriever = None
        
        # Try Qdrant-based retriever
        try:
            from vedabase_retriever import VedabaseRetriever
            self.retriever = VedabaseRetriever()
            self.qdrant_available = True
            logger.info("✅ Qdrant retriever initialized as fallback")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize Qdrant retriever: {e}")
            self.qdrant_available = False
            self.retriever = None
        
        # Try file-based retriever
        try:
            from utils.file_based_retriever import file_retriever
            self.file_retriever = file_retriever
            self.file_retriever_available = True
            logger.info("✅ File-based retriever initialized as fallback")
        except Exception as e:
            logger.warning(f"⚠️ Failed to initialize file-based retriever: {e}")
            self.file_retriever_available = False
            self.file_retriever = None
    
    def query(self, query_text: str, top_k: int = 5) -> Dict[str, Any]:
        """
        Query knowledge base using multi-folder approach for best results.
        
        Args:
            query_text: The query to search for
            top_k: Number of top results to return
            
        Returns:
            Dictionary with response and sources
        """
        logger.info(f"🔍 KnowledgeAgent query: '{query_text}'")
        
        # Priority 1: Multi-folder vector search (most comprehensive)
        if self.multi_folder_available and self.multi_folder_manager:
            try:
                logger.info("🎯 Using multi-folder vector search...")
                results = self.multi_folder_manager.search_all_folders(query_text, top_k=top_k)
                
                if results:
                    # Format results for response
                    response = [result["content"] for result in results]
                    sources = [f"{result['folder']}:{result['collection']}:{result['document_id']}" for result in results]
                    
                    logger.info(f"✅ Multi-folder search found {len(results)} results from {len(set(result['folder'] for result in results))} folders")
                    return {
                        "response": response,
                        "sources": sources,
                        "method": "multi_folder_vector",
                        "folder_count": len(set(result['folder'] for result in results)),
                        "total_results": len(results),
                        "status": 200,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "tags": ["semantic_search", "multi_folder_vector"],
                            "retriever": "multi_folder_vector",
                            "total_results": len(results)
                        }
                    }
                else:
                    logger.warning("⚠️ Multi-folder search returned no results, trying fallback...")
                    
            except Exception as e:
                logger.error(f"❌ Multi-folder search failed: {e}")
        
        # Priority 2: NAS+Qdrant retriever
        if self.nas_available and self.nas_retriever:
            try:
                logger.info("📁 Trying NAS+Qdrant retriever...")
                nas_results = self.nas_retriever.query(query_text, top_k=top_k)
                
                if nas_results:
                    response = [result["content"] for result in nas_results]
                    sources = [f"NAS:{result.get('document_id', 'unknown')}" for result in nas_results]
                    
                    logger.info(f"✅ NAS+Qdrant search found {len(nas_results)} results")
                    return {
                        "response": response,
                        "sources": sources,
                        "method": "nas_qdrant",
                        "folder_count": 1,
                        "total_results": len(nas_results),
                        "status": 200,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "tags": ["semantic_search", "nas_qdrant"],
                            "retriever": "nas_qdrant",
                            "total_results": len(nas_results)
                        }
                    }
                else:
                    logger.warning("⚠️ NAS+Qdrant search returned no results, trying next fallback...")
                    
            except Exception as e:
                logger.error(f"❌ NAS+Qdrant search failed: {e}")
        
        # Priority 3: Qdrant-based retriever
        if self.qdrant_available and self.retriever:
            try:
                logger.info("🗄️ Trying Qdrant retriever...")
                qdrant_results = self.retriever.retrieve(query_text, top_k=top_k)
                
                if qdrant_results:
                    response = [result.page_content for result in qdrant_results]
                    sources = [result.metadata.get("source", "unknown") for result in qdrant_results]
                    
                    logger.info(f"✅ Qdrant search found {len(qdrant_results)} results")
                    return {
                        "response": response,
                        "sources": sources,
                        "method": "qdrant",
                        "folder_count": 1,
                        "total_results": len(qdrant_results),
                        "status": 200,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "tags": ["semantic_search", "qdrant"],
                            "retriever": "qdrant",
                            "total_results": len(qdrant_results)
                        }
                    }
                else:
                    logger.warning("⚠️ Qdrant search returned no results, trying final fallback...")
                    
            except Exception as e:
                logger.error(f"❌ Qdrant search failed: {e}")
        
        # Priority 4: File-based retriever (final fallback)
        if self.file_retriever_available:
            try:
                logger.info("📄 Using file-based retriever as final fallback...")
                file_results = self.file_retriever.search(query_text, limit=top_k)
                
                if file_results:
                    response = [result["text"] for result in file_results]
                    sources = [result.get("source", "file_based") for result in file_results]
                    
                    logger.info(f"✅ File-based search found {len(file_results)} results")
                    return {
                        "response": response,
                        "sources": sources,
                        "method": "file_based",
                        "folder_count": 1,
                        "total_results": len(file_results),
                        "status": 200,
                        "timestamp": datetime.now().isoformat(),
                        "metadata": {
                            "tags": ["semantic_search", "file_based"],
                            "retriever": "file_based",
                            "total_results": len(file_results)
                        }
                    }
                else:
                    logger.warning("⚠️ File-based search also returned no results")
                    
            except Exception as e:
                logger.error(f"❌ File-based search failed: {e}")
        
        # No results from any retriever
        logger.warning("❌ No retrievers available or all failed")
        return {
            "response": ["No relevant information found in any knowledge base."],
            "sources": ["none"],
            "method": "none",
            "folder_count": 0,
            "total_results": 0,
            "status": 404,
            "timestamp": datetime.now().isoformat(),
            "metadata": {
                "tags": ["semantic_search", "none"],
                "retriever": "none",
                "total_results": 0
            }
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get statistics about available knowledge bases."""
        if self.multi_folder_available and self.multi_folder_manager:
            return self.multi_folder_manager.get_folder_statistics()
        else:
            return {
                "status": "Multi-folder manager not available",
                "fallback_retrievers": {
                    "nas_retriever": self.nas_available,
                    "qdrant_retriever": self.qdrant_available,
                    "file_retriever": self.file_retriever_available
                }
            }
    
    def health_check(self) -> Dict[str, Any]:
        """Check health of all knowledge base components."""
        health_status = {
            "multi_folder_manager": self.multi_folder_available,
            "nas_retriever": self.nas_available,
            "qdrant_retriever": self.qdrant_available,
            "file_retriever": self.file_retriever_available
        }
        
        if self.multi_folder_available and self.multi_folder_manager:
            health_status["folder_health"] = self.multi_folder_manager.health_check()
        
        return health_status

    def enhance_with_llm(self, query: str, knowledge_context: str) -> str:
        """Enhanced response using Ollama fallback if configured, else local formatting."""
        try:
            # Try Ollama when configured
            import requests
            ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
            ollama_model = os.getenv("OLLAMA_MODEL", "llama3-8b-8192")
            if ollama_url and ollama_model:
                prompt = (
                    "You are a helpful assistant. Use the following knowledge context if available to answer the query.\n\n"
                    f"Query: {query}\n\n"
                    f"Knowledge Context:\n{knowledge_context}\n\n"
                    "If the context is empty or irrelevant, give a general helpful answer. Keep it clear and concise."
                )
                payload = {"model": ollama_model, "prompt": prompt, "stream": False}
                headers = {"Content-Type": "application/json"}
                r = requests.post(ollama_url, json=payload, headers=headers, timeout=int(os.getenv("OLLAMA_TIMEOUT", "60")))
                if r.status_code == 200:
                    data = r.json()
                    text = data.get("response") or data.get("message", {}).get("content")
                    if text:
                        return text.strip()

            # Fallback: local formatting and summarization
            if knowledge_context.strip():
                # Simple summarization: find sentences with the most query words
                query_words = set(query.lower().split())
                sentences = knowledge_context.split('.')
                sentence_scores = []
                for sentence in sentences:
                    if not sentence.strip():
                        continue
                    sentence_words = set(sentence.lower().split())
                    score = len(query_words.intersection(sentence_words))
                    sentence_scores.append((score, sentence))

                sentence_scores.sort(key=lambda x: x[0], reverse=True)

                # Return the top 3 sentences
                top_sentences = [s for score, s in sentence_scores[:3] if score > 0]

                if top_sentences:
                    return ". ".join(top_sentences).strip() + "."
                else:
                    # If no sentences have query words, return the first 3 sentences
                    return ". ".join(sentences[:3]).strip() + "."

            return f"I don't have specific information about '{query}' in the knowledge base."
        except Exception as e:
            logger.error(f"LLM enhancement failed: {str(e)}")
            return knowledge_context if knowledge_context.strip() else "Unable to process your query at this time."

    def run(self, input_path: str, live_feed: str = "", model: str = "knowledge_agent", input_type: str = "text", task_id: str = None) -> Dict[str, Any]:
        """Main entry point for agent execution - compatible with existing agent interface."""
        task_id = task_id or str(uuid.uuid4())
        logger.info(f"KnowledgeAgent processing task {task_id}, query: {input_path}")

        # Use input_path as the query text
        query_result = self.query(input_path, top_k=5)

        # Format response to match expected agent output format
        if query_result.get("status", 200) == 200 and query_result.get("response"):
            # Combine knowledge base results
            if isinstance(query_result["response"], list) and query_result["response"]:
                combined_text = "\n\n".join(query_result["response"][:3])
            else:
                combined_text = str(query_result["response"])

            # Enhance with LLM for better formatting and context
            enhanced_response = self.enhance_with_llm(input_path, combined_text)

            return {
                "response": enhanced_response,
                "query_id": task_id,
                "query": input_path,
                "sources": query_result.get("sources", []),
                "metadata": query_result.get("metadata", {}),
                "timestamp": query_result.get("timestamp", datetime.now().isoformat()),
                "status": 200,
                "model": model,
                "knowledge_base_results": len(query_result.get("response", [])) if isinstance(query_result.get("response"), list) else 1,
                "endpoint": "knowledge_agent"
            }
        else:
            # Fallback to LLM only if no knowledge base results
            try:
                fallback_response = self.enhance_with_llm(input_path, "No specific knowledge found in database.")
                return {
                    "response": fallback_response,
                    "query_id": task_id,
                    "query": input_path,
                    "sources": [],
                    "metadata": {},
                    "timestamp": datetime.now().isoformat(),
                    "status": 200,
                    "model": model,
                    "knowledge_base_results": 0,
                    "fallback": True,
                    "endpoint": "knowledge_agent"
                }
            except Exception:
                return {
                    "response": "I couldn't find relevant information in the knowledge base for your query.",
                    "query_id": task_id,
                    "query": input_path,
                    "sources": [],
                    "metadata": {},
                    "timestamp": datetime.now().isoformat(),
                    "status": 404,
                    "model": model,
                    "error": query_result.get("error", "No results found"),
                    "endpoint": "knowledge_agent"
                }