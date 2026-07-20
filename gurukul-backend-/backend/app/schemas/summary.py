from pydantic import BaseModel
from typing import Optional, List, Dict
from app.schemas.chat import YouTubeVideo

# --- Subject Explorer ---
class SubjectExplorerRequest(BaseModel):
    subject: str
    topic: str
    provider: Optional[str] = "groq"
    use_knowledge_store: Optional[bool] = False

class SubjectExplorerResponse(BaseModel):
    subject: str
    topic: str
    notes: str
    provider: str
    youtube_recommendations: List[YouTubeVideo]
    success: bool

# --- Summarizer ---
class SummarizerRequest(BaseModel):
    text: Optional[str] = None
    provider: Optional[str] = "groq"
    summary_type: Optional[str] = "concise"

class SummarizerResponse(BaseModel):
    original_length: int
    summary: str
    summary_length: int
    provider: str
    summary_type: str
    success: bool

class PDFPageSummary(BaseModel):
    page_number: int
    summary: str
    original_length: int
    summary_length: int

class PDFSummarizerResponse(BaseModel):
    total_pages: int
    pages_summarized: int
    page_summaries: List[PDFPageSummary]
    overall_summary: str
    summary_type: str
    provider: str
    success: bool

class DOCSectionSummary(BaseModel):
    section_number: int
    summary: str
    original_length: int
    summary_length: int

class DOCSummarizerResponse(BaseModel):
    total_sections: int
    sections_summarized: int
    section_summaries: List[DOCSectionSummary]
    overall_summary: str
    summary_type: str
    provider: str
    success: bool

class SaveSummaryRequest(BaseModel):
    title: str
    content: str
    source: Optional[str] = None
    source_type: Optional[str] = None
    metadata: Optional[Dict] = None

class SavedSummary(BaseModel):
    summary_id: str
    title: str
    content: str
    source: Optional[str]
    source_type: Optional[str]
    created_at: str
    updated_at: str
    question_count: int
    metadata: Optional[Dict]
