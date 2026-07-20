"""
Vector Store Service for RAG (Retrieval Augmented Generation)
Replaces in-memory dictionary with persistent vector database

NOTE: Disabled in lightweight deployment (no sentence-transformers).
"""

from typing import List, Dict, Optional, Any
import os
import json
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

# Optional ML imports
try:
    from sentence_transformers import SentenceTransformer
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    SentenceTransformer = None
    logger.warning("sentence-transformers not installed. VectorStoreService disabled.")

class VectorStoreService:
    """
    Vector Store Service that supports multiple backends:
    - ChromaDB (default, easiest to start)
    - FAISS (fast, CPU-based)
    - Qdrant (production-ready)
    """
    
    def __init__(self, backend: str = "chromadb", collection_name: str = "knowledge_base"):
        """
        Initialize vector store service
        
        Args:
            backend: Vector database backend ("chromadb", "faiss", "qdrant")
            collection_name: Name of the collection/namespace
        """
        if not ML_AVAILABLE:
            logger.warning("VectorStoreService disabled - sentence-transformers not installed")
            self.embedding_model = None
            self.client = None
            self.collection = None
            return
            
        self.backend = backend.lower()
        self.collection_name = collection_name
        
        # Initialize embedding model (384 dimensions)
        logger.info(f"Loading embedding model: all-MiniLM-L6-v2")
        self.embedding_model = SentenceTransformer('all-MiniLM-L6-v2')
        
        # Initialize vector database based on backend
        if self.backend == "chromadb":
            self._init_chromadb()
        elif self.backend == "faiss":
            self._init_faiss()
        elif self.backend == "qdrant":
            self._init_qdrant()
        else:
            raise ValueError(f"Unsupported backend: {backend}. Use 'chromadb', 'faiss', or 'qdrant'")
    
    def _init_chromadb(self):
        """Initialize ChromaDB (persistent, file-based)"""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Create directory if it doesn't exist
            db_path = "./knowledge_store/chroma_db"
            os.makedirs(db_path, exist_ok=True)
            
            # Initialize ChromaDB client
            self.client = chromadb.PersistentClient(
                path=db_path,
                settings=Settings(anonymized_telemetry=False)
            )
            
            # Get or create collection
            self.collection = self.client.get_or_create_collection(
                name=self.collection_name,
                metadata={"description": "Gurukul Knowledge Base"}
            )
            
            logger.info(f"ChromaDB initialized: {db_path}")
        except ImportError:
            raise ImportError("chromadb not installed. Run: pip install chromadb")
        except Exception as e:
            logger.error(f"Failed to initialize ChromaDB: {e}")
            raise
    
    def _init_faiss(self):
        """Initialize FAISS (fast similarity search)"""
        try:
            import faiss
            import numpy as np
            
            # Create directory if it doesn't exist
            os.makedirs("./vector_stores/faiss", exist_ok=True)
            
            # FAISS index for 384-dimensional vectors
            dimension = 384
            self.index = faiss.IndexFlatL2(dimension)  # L2 distance
            
            # Store metadata separately (FAISS only stores vectors)
            self.metadata_store = []
            self.index_path = f"./vector_stores/faiss/{self.collection_name}.index"
            self.metadata_path = f"./vector_stores/faiss/{self.collection_name}_metadata.json"
            
            # Load existing index if it exists
            if os.path.exists(self.index_path):
                self.index = faiss.read_index(self.index_path)
                with open(self.metadata_path, 'r') as f:
                    self.metadata_store = json.load(f)
                logger.info(f"Loaded existing FAISS index: {len(self.metadata_store)} vectors")
            else:
                logger.info("Creating new FAISS index")
            
            logger.info("FAISS initialized")
        except ImportError:
            raise ImportError("faiss-cpu not installed. Run: pip install faiss-cpu")
        except Exception as e:
            logger.error(f"Failed to initialize FAISS: {e}")
            raise
    
    def _init_qdrant(self):
        """Initialize Qdrant (production vector database)"""
        try:
            from qdrant_client import QdrantClient
            from qdrant_client.models import Distance, VectorParams
            
            # For local development, use in-memory or file-based
            # For production, use Qdrant cloud or server
            self.client = QdrantClient(path="./knowledge_store/qdrant")
            
            # Create collection if it doesn't exist
            try:
                self.client.get_collection(self.collection_name)
            except:
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
            
            logger.info("Qdrant initialized")
        except ImportError:
            raise ImportError("qdrant-client not installed. Run: pip install qdrant-client")
        except Exception as e:
            logger.error(f"Failed to initialize Qdrant: {e}")
            raise
    
    def add_knowledge(
        self, 
        text: str, 
        metadata: Optional[Dict[str, Any]] = None,
        chunk_size: int = 500,
        chunk_overlap: int = 50
    ) -> Dict[str, Any]:
        """
        Add knowledge to vector store
        
        Args:
            text: Text content to store
            metadata: Optional metadata (source, subject, topic, etc.)
            chunk_size: Split long text into chunks of this size
            chunk_overlap: Overlap between chunks for context
        
        Returns:
            Dict with status and number of chunks added
        """
        if not text or not isinstance(text, str):
            raise ValueError("Text must be a non-empty string")
        
        # Prepare metadata
        if metadata is None:
            metadata = {}
        
        metadata["added_at"] = datetime.now().isoformat()
        
        # Split text into chunks if it's too long
        chunks = self._chunk_text(text, chunk_size, chunk_overlap)
        
        chunks_added = 0
        
        for i, chunk in enumerate(chunks):
            try:
                # Generate embedding for this chunk
                embedding = self.embedding_model.encode(chunk).tolist()
                
                # Add chunk metadata
                chunk_metadata = metadata.copy()
                chunk_metadata["chunk_index"] = i
                chunk_metadata["total_chunks"] = len(chunks)
                
                # Store in vector database
                if self.backend == "chromadb":
                    self.collection.add(
                        embeddings=[embedding],
                        documents=[chunk],
                        metadatas=[chunk_metadata],
                        ids=[f"{self.collection_name}_{datetime.now().timestamp()}_{i}"]
                    )
                
                elif self.backend == "faiss":
                    import numpy as np
                    # Add vector to FAISS index
                    vector = np.array([embedding], dtype='float32')
                    self.index.add(vector)
                    
                    # Store metadata
                    self.metadata_store.append({
                        "text": chunk,
                        "metadata": chunk_metadata
                    })
                    
                    # Save index and metadata
                    import faiss
                    faiss.write_index(self.index, self.index_path)
                    with open(self.metadata_path, 'w') as f:
                        json.dump(self.metadata_store, f)
                
                elif self.backend == "qdrant":
                    from qdrant_client.models import PointStruct
                    self.client.upsert(
                        collection_name=self.collection_name,
                        points=[
                            PointStruct(
                                id=len(self.metadata_store) if hasattr(self, 'metadata_store') else 0,
                                vector=embedding,
                                payload={"text": chunk, **chunk_metadata}
                            )
                        ]
                    )
                
                chunks_added += 1
                
            except Exception as e:
                logger.error(f"Failed to add chunk {i}: {e}")
                continue
        
        logger.info(f"Added {chunks_added} chunks to vector store")
        return {
            "status": "success",
            "chunks_added": chunks_added,
            "total_chunks": len(chunks)
        }
    
    def search(
        self, 
        query: str, 
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        Search for similar content using semantic search
        
        Args:
            query: Search query text
            top_k: Number of results to return
            filter_metadata: Optional metadata filters (e.g., {"subject": "Physics"})
        
        Returns:
            List of results with text, metadata, and similarity score
        """
        if not query:
            return []
        
        # Generate embedding for query
        query_embedding = self.embedding_model.encode(query).tolist()
        
        results = []
        
        try:
            if self.backend == "chromadb":
                # Build where clause for filtering
                where_clause = None
                if filter_metadata:
                    if len(filter_metadata) == 1:
                        where_clause = filter_metadata
                    elif len(filter_metadata) > 1:
                        # ChromaDB requires explicit logical $and list for multiple conditions
                        where_clause = {"$and": [{k: v} for k, v in filter_metadata.items()]}
                
                # Search in ChromaDB
                search_results = self.collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_clause
                )
                
                # Format results
                if search_results['documents'] and len(search_results['documents'][0]) > 0:
                    for i in range(len(search_results['documents'][0])):
                        results.append({
                            "text": search_results['documents'][0][i],
                            "metadata": search_results['metadatas'][0][i] if search_results['metadatas'] else {},
                            "score": 1 - search_results['distances'][0][i] if search_results['distances'] else 0.0
                        })
            
            elif self.backend == "faiss":
                import numpy as np
                import faiss
                
                # Search in FAISS
                query_vector = np.array([query_embedding], dtype='float32')
                k = min(top_k, self.index.ntotal) if self.index.ntotal > 0 else 0
                
                if k > 0:
                    distances, indices = self.index.search(query_vector, k)
                    
                    for idx, distance in zip(indices[0], distances[0]):
                        if idx < len(self.metadata_store):
                            result = {
                                "text": self.metadata_store[idx]["text"],
                                "metadata": self.metadata_store[idx]["metadata"],
                                "score": 1 / (1 + distance)  # Convert distance to similarity
                            }
                            
                            # Apply metadata filter if provided
                            if filter_metadata:
                                if all(result["metadata"].get(k) == v for k, v in filter_metadata.items()):
                                    results.append(result)
                            else:
                                results.append(result)
            
            elif self.backend == "qdrant":
                from qdrant_client.models import Filter, FieldCondition, MatchValue
                
                # Build filter if provided
                query_filter = None
                if filter_metadata:
                    conditions = [
                        FieldCondition(key=k, match=MatchValue(value=v))
                        for k, v in filter_metadata.items()
                    ]
                    query_filter = Filter(must=conditions)
                
                # Search in Qdrant
                search_results = self.client.search(
                    collection_name=self.collection_name,
                    query_vector=query_embedding,
                    limit=top_k,
                    query_filter=query_filter
                )
                
                # Format results
                for result in search_results:
                    results.append({
                        "text": result.payload.get("text", ""),
                        "metadata": {k: v for k, v in result.payload.items() if k != "text"},
                        "score": result.score
                    })
        
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []
        
        return results
    
    def get_context(self, query: str, top_k: int = 3) -> str:
        """
        Get formatted context string for RAG
        
        Args:
            query: User query
            top_k: Number of relevant chunks to retrieve
        
        Returns:
            Formatted context string ready to add to LLM prompt
        """
        results = self.search(query, top_k=top_k)
        
        if not results:
            return ""
        
        context_parts = []
        for i, result in enumerate(results, 1):
            context_parts.append(
                f"[Context {i}] {result['text']}\n"
                f"Source: {result['metadata'].get('source', 'Unknown')}"
            )
        
        return "\n\n".join(context_parts)
    
    def _chunk_text(self, text: str, chunk_size: int, chunk_overlap: int) -> List[str]:
        """
        Split text into overlapping chunks
        
        Args:
            text: Text to chunk
            chunk_size: Size of each chunk (characters)
            chunk_overlap: Overlap between chunks
        
        Returns:
            List of text chunks
        """
        if len(text) <= chunk_size:
            return [text]
        
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + chunk_size
            chunk = text[start:end]
            
            # Try to break at sentence boundary
            if end < len(text):
                last_period = chunk.rfind('.')
                last_newline = chunk.rfind('\n')
                break_point = max(last_period, last_newline)
                
                if break_point > chunk_size * 0.5:  # Only break if we're past halfway
                    chunk = chunk[:break_point + 1]
                    end = start + break_point + 1
            
            chunks.append(chunk.strip())
            start = end - chunk_overlap
        
        return chunks
    
    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about the vector store"""
        try:
            if self.backend == "chromadb":
                count = self.collection.count()
                return {
                    "backend": "chromadb",
                    "collection": self.collection_name,
                    "total_documents": count
                }
            elif self.backend == "faiss":
                return {
                    "backend": "faiss",
                    "collection": self.collection_name,
                    "total_vectors": self.index.ntotal if hasattr(self, 'index') else 0
                }
            elif self.backend == "qdrant":
                collection_info = self.client.get_collection(self.collection_name)
                return {
                    "backend": "qdrant",
                    "collection": self.collection_name,
                    "total_vectors": collection_info.points_count
                }
        except Exception as e:
            logger.error(f"Failed to get stats: {e}")
            return {"error": str(e)}
    
    def clear_collection(self):
        """Clear all data from the collection"""
        try:
            if self.backend == "chromadb":
                self.client.delete_collection(self.collection_name)
                self.collection = self.client.create_collection(name=self.collection_name)
            elif self.backend == "faiss":
                import faiss
                dimension = 384
                self.index = faiss.IndexFlatL2(dimension)
                self.metadata_store = []
                if os.path.exists(self.index_path):
                    os.remove(self.index_path)
                if os.path.exists(self.metadata_path):
                    os.remove(self.metadata_path)
            elif self.backend == "qdrant":
                self.client.delete_collection(self.collection_name)
                from qdrant_client.models import VectorParams, Distance
                self.client.create_collection(
                    collection_name=self.collection_name,
                    vectors_config=VectorParams(size=384, distance=Distance.COSINE)
                )
            logger.info(f"Cleared collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"Failed to clear collection: {e}")
            raise
