from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional, List, Dict
import uuid
import logging
from collections import defaultdict
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.database import get_db
from app.routers.auth import get_current_user
from app.models.all_models import User
from app.services.knowledge_base_helper import get_knowledge_base_context, enhance_prompt_with_context
from app.services.pravah_adapter import pravah_adapter
from app.services.bucket_adapter import bucket_adapter

logger = logging.getLogger(__name__)
router = APIRouter()

# In-memory chat history storage (per user and conversation - resets on server restart)
# Format: {f"{user_id}:{conversation_id}": [messages]}
# For production, this should be stored in PostgreSQL
_chat_history: Dict[str, List[dict]] = defaultdict(list)

# Initialize vector store service (lazy loading) - kept for backward compatibility
_vector_store_instance = None

def get_vector_store():
    """Get or create vector store instance (backward compatibility)"""
    from app.services.knowledge_base_helper import get_vector_store as _get_vector_store
    return _get_vector_store()

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    provider: str = "auto"
    use_rag: bool = True

@router.get("/health")
async def health():
    return {"status": "ok"}

@router.post("")  # Mounts at /api/v1/chat
async def chat_endpoint(
    request: ChatRequest,
    current_user: User = Depends(get_current_user)
):
    """
    Chat Endpoint with RAG (Retrieval Augmented Generation) support
    Uses Knowledge Base + Groq with automatic fallback to Groq-only if KB fails
    """
    # Scope conversation_id to user to prevent cross-user access
    conversation_id = request.conversation_id or str(uuid.uuid4())
    user_conversation_key = f"{current_user.id}:{conversation_id}"
    
    # Resolve user's active syllabus preferences from their profile
    board = None
    medium = None
    class_std = None
    if current_user and current_user.profile and isinstance(current_user.profile.data, dict):
        profile_data = current_user.profile.data
        board = profile_data.get("board")
        medium = profile_data.get("medium")
        class_std = profile_data.get("class") or profile_data.get("class_std") or profile_data.get("class_standard")
    
    # Emit Signal: User interaction started
    pravah_adapter.emit_signal(
        event_type="user_action",
        action="chat_request",
        payload={
            "conversation_id": conversation_id, 
            "use_rag": request.use_rag,
            "message": request.message,
            "board": board,
            "medium": medium,
            "class_std": class_std
        }
    )
    
    # Delegate to Uniguru if requested
    if request.provider and request.provider.lower() == "uniguru":
        import httpx
        import os
        
        # Load local Uniguru settings or default (Uniguru backend runs on port 8000 by default)
        uniguru_url = os.getenv("UNIGURU_API_URL", "http://localhost:8000/ask")
        uniguru_token = os.getenv("UNIGURU_API_TOKEN", "UG_x8K29dkL92msPq")
        previous_messages = _chat_history.get(user_conversation_key, [])
        
        headers = {
            "Authorization": f"Bearer {uniguru_token}",
            "X-Caller-Name": "gurukul-platform",
            "Content-Type": "application/json"
        }
        
        payload = {
            "query": request.message,
            "session_id": conversation_id,
            "context": {
                "caller": "gurukul-platform",
                "timestamp": str(uuid.uuid4())
            }
        }
        
        try:
            async with httpx.AsyncClient() as client:
                response = await client.post(uniguru_url, json=payload, headers=headers, timeout=30.0)
                if response.status_code == 200:
                    data = response.json()
                    response_text = data.get("answer", "No response from Uniguru.")
                else:
                    response_text = f"Uniguru returned error {response.status_code}: {response.text}"
        except Exception as e:
            response_text = f"Failed to connect to Uniguru: {str(e)}"
            
        # Save messages to chat history (scoped to user)
        _chat_history[user_conversation_key].append({"role": "user", "content": request.message})
        _chat_history[user_conversation_key].append({"role": "assistant", "content": response_text})
        
        # Emit Memory to Bucket (tantra telemetry)
        bucket_adapter.emit_memory(
            user_id=str(current_user.id),
            session_id=conversation_id,
            action="chat_interaction",
            outcome="success",
            payload={
                "message_len": len(request.message),
                "response_len": len(response_text),
                "rag_used": True,
                "provider": "uniguru"
            }
        )
        
        # Emit Signal: Interaction complete
        pravah_adapter.emit_signal(
            event_type="user_action",
            action="chat_response_generated",
            status="success"
        )
        
        return {
            "response": response_text,
            "conversation_id": conversation_id,
            "knowledge_base_used": True,
            "groq_used": False,
            "context_length": len(response_text),
            "fallback_used": False,
            "kb_error": None,
            "groq_error": None,
            "history_messages_used": len(previous_messages)
        }
    
    fallback_used = False
    fallback_context_warning = ""
    filter_metadata = None
    
    # Step 1: Resolve user's active syllabus preferences from their profile
    if request.use_rag:
        if board:
            filter_metadata = {
                "board": board.upper(),
                "medium": medium.lower() if medium else "en",
                "class_std": int(class_std) if class_std else 10
            }

        # Query database with strict user board filter
        kb_result = get_knowledge_base_context(
            query=request.message,
            top_k=3,
            filter_metadata=filter_metadata,
            use_knowledge_base=True
        )
        
        # Step 2: Handle fallback if no matching context is found for active board
        if filter_metadata and not kb_result["context"] and filter_metadata["board"] != "NCERT":
            # Fall back deterministically to NCERT English Standard 10
            ncert_fallback_filter = {
                "board": "NCERT",
                "medium": "en",
                "class_std": 10
            }
            logger.info(f"RAG search returned 0 matches for {filter_metadata}. Triggering non-silent fallback to NCERT English Std 10.")
            
            kb_result = get_knowledge_base_context(
                query=request.message,
                top_k=3,
                filter_metadata=ncert_fallback_filter,
                use_knowledge_base=True
            )
            
            if kb_result["context"]:
                fallback_used = True
                fallback_context_warning = (
                    f"\n\n[FALLBACK SYSTEM WARNING] This context is sourced from NCERT (CBSE) English Standard 10 "
                    f"due to missing active syllabus chunks for Board {filter_metadata['board']} Medium {filter_metadata['medium']} Standard {filter_metadata['class_std']}."
                )
                kb_result["context"] = kb_result["context"] + fallback_context_warning
    else:
        kb_result = {
            "context": "",
            "knowledge_base_used": False,
            "results": [],
            "error": None
        }
    
    # Step 3: Build system message with or without context
    base_system_message = "You are Gurukul, an AI coding tutor and educational guide."
    
    if kb_result["knowledge_base_used"] and kb_result["context"]:
        # Best case: Use both Knowledge Base + Groq
        system_message = enhance_prompt_with_context(
            base_prompt=base_system_message,
            query=request.message,
            context=kb_result["context"],
            include_context_instruction=True
        )
        if fallback_used:
            system_message += (
                "\n\nCRITICAL CONTEXT DISCIPLINE: Sourced from NCERT CBSE English Standard 10 "
                "due to missing active board chunks. You MUST explicitly inform the user that this context "
                "is a fallback sourced from NCERT (CBSE) and not their active board."
            )
        logger.info(f"Using Knowledge Base + Groq: {len(kb_result['context'])} chars context")
    else:
        # Fallback: Use Groq only (KB failed or disabled)
        system_message = base_system_message
        if kb_result["error"]:
            logger.warning(f"Knowledge Base unavailable, using Groq only: {kb_result['error']}")
        else:
            logger.info("Knowledge Base disabled or empty, using Groq only")
    
    # Step 4: Build message history for context
    # Retrieve previous messages from this conversation
    previous_messages = _chat_history.get(user_conversation_key, [])
    
    # Build messages array with conversation history
    messages = [{"role": "system", "content": system_message}]
    
    # Add previous conversation history (limit to last 10 messages to avoid token limits)
    max_history = 10
    if len(previous_messages) > max_history:
        # Keep the most recent messages
        messages.extend(previous_messages[-max_history:])
    else:
        messages.extend(previous_messages)
    
    # Add current user message
    messages.append({"role": "user", "content": request.message})
    
    # Step 5: Call Groq with conversation history
    try:
        from groq import Groq
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=messages,
            temperature=0.7,
            max_tokens=1024,
            top_p=1,
            stream=False,
            stop=None,
        )
        
        response_text = completion.choices[0].message.content
        groq_used = True
        groq_error = None
        
    except Exception as e:
        logger.error(f"Groq Error: {e}")
        response_text = f"I'm sorry, I'm having trouble connecting to my brain right now. (Error: {str(e)})"
        groq_used = False
        groq_error = str(e)
    
    # Save messages to chat history (scoped to user)
    _chat_history[user_conversation_key].append({"role": "user", "content": request.message})
    _chat_history[user_conversation_key].append({"role": "assistant", "content": response_text})
    
    # Emit Memory to Bucket
    bucket_adapter.emit_memory(
        user_id=str(current_user.id),
        session_id=conversation_id,
        action="chat_interaction",
        outcome="success" if groq_used else "failure",
        payload={
            "message_len": len(request.message),
            "response_len": len(response_text),
            "rag_used": kb_result["knowledge_base_used"]
        }
    )

    import hashlib
    oh_val = hashlib.sha256(response_text.encode('utf-8')).hexdigest()
    run_id_val = f"api-session-{conversation_id[:8]}"
    rv_val = hashlib.sha256(f"{response_text}:{run_id_val}".encode('utf-8')).hexdigest()
    retrieved_doc_ids = [res.get('metadata', {}).get('id', 'Unknown') for res in kb_result.get('results', [])] if kb_result.get('results') else []

    # Emit Signal: Interaction complete
    pravah_adapter.emit_signal(
        event_type="user_action",
        action="chat_response_generated",
        status="success" if groq_used else "failure",
        payload={
            "conversation_id": conversation_id,
            "response": response_text,
            "run_id": run_id_val,
            "prompt": request.message,
            "retrieval_context": kb_result.get("context", ""),
            "retrieved_document_ids": retrieved_doc_ids,
            "model_identifier": "Groq Llama 3.3 70B" if groq_used else "None",
            "model_version": settings.GROQ_MODEL_NAME if groq_used else "1.0.0",
            "inference_configuration": {"temperature": 0.0, "max_tokens": 1024},
            "output_hash": oh_val,
            "replay_verification": rv_val
        }
    )
    
    return {
        "response": response_text,
        "conversation_id": conversation_id,
        "knowledge_base_used": kb_result["knowledge_base_used"],
        "groq_used": groq_used,
        "context_length": len(kb_result["context"]) if kb_result["context"] else 0,
        "fallback_used": fallback_used,
        "kb_error": kb_result["error"] if not kb_result["knowledge_base_used"] else None,
        "groq_error": groq_error,
        "history_messages_used": len(previous_messages)
    }

@router.get("/history/{conversation_id}")
async def get_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Return actual chat history for conversation (user-scoped)"""
    # Scope conversation_id to user to prevent cross-user access
    user_conversation_key = f"{current_user.id}:{conversation_id}"
    messages = _chat_history.get(user_conversation_key, [])
    
    if not messages:
        # Return empty list if no history found (don't return mock data)
        return {"messages": [], "found": False}
    
    return {"messages": messages, "found": True}

@router.delete("/history/{conversation_id}")
async def delete_chat_history(
    conversation_id: str,
    current_user: User = Depends(get_current_user)
):
    """Delete chat history for conversation (user-scoped)"""
    # Scope conversation_id to user to prevent cross-user access
    user_conversation_key = f"{current_user.id}:{conversation_id}"
    if user_conversation_key in _chat_history:
        del _chat_history[user_conversation_key]
        return {"status": "deleted", "found": True}
    return {"status": "deleted", "found": False}

class KnowledgeRequest(BaseModel):
    text: str
    metadata: Optional[dict] = {}

@router.post("/knowledge")
async def add_knowledge(request: KnowledgeRequest):
    """
    Add knowledge to vector store for RAG
    Replaces the old in-memory dictionary storage
    """
    if not request.text or len(request.text.strip()) < 10:
        raise HTTPException(status_code=400, detail="Text must be at least 10 characters")
    
    try:
        vector_store = get_vector_store()
        if not vector_store:
            raise HTTPException(
                status_code=503, 
                detail="Vector store not available. Check backend configuration."
            )
        
        result = vector_store.add_knowledge(
            text=request.text,
            metadata=request.metadata or {}
        )
        
        logger.info(f"Knowledge added: {result['chunks_added']} chunks")
        
        return {
            "status": "learned",
            "chunks_added": result["chunks_added"],
            "total_chunks": result["total_chunks"],
            "backend": settings.VECTOR_STORE_BACKEND
        }
    
    except Exception as e:
        logger.error(f"Failed to add knowledge: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to add knowledge: {str(e)}")
