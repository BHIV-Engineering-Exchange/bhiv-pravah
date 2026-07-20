from pydantic import BaseModel
from typing import Optional, List, Dict

# --- Questions & Flashcards ---
class QuestionGenerationRequest(BaseModel):
    summary_id: str
    question_types: Optional[List[str]] = ["qa", "mcq", "flashcard", "case_based"]
    num_questions: Optional[int] = 5
    difficulty: Optional[str] = "medium"

class MCQOption(BaseModel):
    option: str
    is_correct: bool

class Question(BaseModel):
    question_id: str
    summary_id: str
    question_type: str
    question: str
    answer: str
    options: Optional[List[MCQOption]] = None
    explanation: Optional[str] = None
    difficulty: str
    created_at: str

class QuestionGenerationResponse(BaseModel):
    summary_id: str
    questions: List[Question]
    total_questions: int
    success: bool

class GenerateFlashcardsRequest(BaseModel):
    title: str
    content: str
    date: str
    question_type: str = "conceptual"

class Flashcard(BaseModel):
    question_id: str
    question: str
    answer: str
    question_type: str = "conceptual"
    days_until_review: int = 0
    confidence: float = 0.0
