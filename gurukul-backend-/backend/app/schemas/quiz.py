from pydantic import BaseModel
from typing import Optional, List, Dict

# --- Review Models ---
class ReviewSchedule(BaseModel):
    question_id: str
    summary_id: str
    first_review: str
    second_review: str
    third_review: str
    last_review_date: Optional[str] = None
    next_review_date: str
    review_count: int = 0
    mastery_level: str = "learning"

class ReviewRequest(BaseModel):
    question_id: str
    user_answer: Optional[str] = None
    is_correct: bool
    confidence: Optional[str] = "medium"

class ReviewResponse(BaseModel):
    question_id: str
    correct_answer: str
    is_correct: bool
    next_review_date: str
    review_count: int
    mastery_level: str
    message: str

class PendingReview(BaseModel):
    question_id: str
    summary_id: str
    question: str
    question_type: str
    answer: str
    next_review_date: str
    days_until_review: int

# --- Quiz Models ---
class QuizRequest(BaseModel):
    subject: str
    topic: str
    provider: Optional[str] = "auto"
    difficulty: Optional[str] = "medium"

class QuizQuestion(BaseModel):
    question_id: str
    question_number: int
    question: str
    options: List[str]
    question_type: str

class QuizResponse(BaseModel):
    quiz_id: str
    subject: str
    topic: str
    questions: List[QuizQuestion]
    total_questions: int
    created_at: str
    provider: str

class QuizSubmission(BaseModel):
    quiz_id: str
    answers: Dict[str, str]

class QuizResult(BaseModel):
    quiz_id: str
    total_questions: int
    correct_answers: int
    wrong_answers: int
    score_percentage: float
    results: List[Dict]
    submitted_at: str
