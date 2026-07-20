from pydantic import BaseModel
from typing import Optional, List, Dict

# --- Youtube Models ---
class YouTubeVideo(BaseModel):
    title: str
    video_id: str
    url: str
    thumbnail: str
    channel_title: str
    duration: Optional[str] = None
    view_count: Optional[str] = None

# --- Chat Models ---
class ChatMessage(BaseModel):
    role: str  # "user" or "assistant"
    content: str
    timestamp: Optional[str] = None

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[str] = None
    provider: Optional[str] = "auto"
    use_rag: Optional[bool] = True
    max_history: Optional[int] = 10

class ChatResponse(BaseModel):
    response: str
    conversation_id: str
    provider: str
    message_count: int
    timestamp: str
    success: bool

class ConversationHistory(BaseModel):
    conversation_id: str
    messages: List[ChatMessage]
    created_at: str
    updated_at: str
    message_count: int
