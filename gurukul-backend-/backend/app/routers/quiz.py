from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from typing import Optional, Dict, List
from app.routers.auth import get_current_user
from app.models.all_models import User, TestResult
from app.core.database import get_db
from app.core.config import settings
from app.services.ems_sync import ems_sync
from app.services.knowledge_base_helper import get_knowledge_base_context, enhance_prompt_with_context
from app.utils.grade_helper import get_student_grade, get_grade_complexity_guidelines, get_grade_level_description
from sqlalchemy.orm import Session
import uuid
from datetime import datetime
import logging

logger = logging.getLogger(__name__)

router = APIRouter()

# In-memory storage for quizzes (temporary until submission)
quiz_store = {}

class QuizGenerateRequest(BaseModel):
    subject: str
    topic: str
    difficulty: str = "medium"
    provider: str = "auto"
    num_questions: int = 10

class QuizSubmitRequest(BaseModel):
    quiz_id: str
    answers: Dict[str, str]  # {question_id: "A" | "B" | "C" | "D"}

@router.post("/generate")
async def generate_quiz(request: QuizGenerateRequest, current_user: User = Depends(get_current_user), db: Session = Depends(get_db)):
    """
    Generate a quiz using Knowledge Base + Groq with automatic fallback to Groq-only if KB fails
    """
    # Get student's grade for grade-level appropriate questions
    grade = await get_student_grade(current_user, db)
    grade_description = get_grade_level_description(grade)
    complexity_guidelines = get_grade_complexity_guidelines(grade)
    
    if grade:
        logger.info(f"Generating quiz for Grade {grade} student ({current_user.email})")
    else:
        logger.info(f"Grade not available for {current_user.email}, using default intermediate level")
    
    # Step 1: Try to get relevant knowledge from knowledge base
    kb_result = get_knowledge_base_context(
        query=f"{request.subject} {request.topic}",
        top_k=5,
        filter_metadata={"subject": request.subject} if request.subject else None,
        use_knowledge_base=True
    )
    
    # Step 2: Build quiz generation prompt (with or without KB context)
    base_prompt = f"""Generate exactly {request.num_questions} multiple-choice quiz questions (MCQs) about {request.subject} - {request.topic}.

STUDENT GRADE LEVEL: {grade_description}
{complexity_guidelines}

IMPORTANT: Adjust question complexity, vocabulary, and answer choices to be appropriate for a {grade_description} student.
- Use age-appropriate language and terminology
- Ensure questions are challenging but not overwhelming for this grade level
- Answer choices should be plausible but clearly distinguishable for this grade level

Requirements:
- Difficulty level: {request.difficulty} (adjusted for {grade_description} level)
- Each question must have exactly 4 options (A, B, C, D)
- Only one option should be correct
- Questions should test understanding of key concepts appropriate for {grade_description}
- Format your response as JSON with this structure:
{{
  "questions": [
    {{
      "question": "Question text here?",
      "options": {{"A": "Option A text", "B": "Option B text", "C": "Option C text", "D": "Option D text"}},
      "correct_answer": "A",
      "explanation": "Brief explanation of why this is correct"
    }}
  ]
}}

Generate {request.num_questions} questions now:"""
    
    if kb_result["knowledge_base_used"] and kb_result["context"]:
        # Best case: Use Knowledge Base context + Groq
        prompt = enhance_prompt_with_context(
            base_prompt=base_prompt,
            query=f"Generate quiz questions about {request.topic}",
            context=kb_result["context"],
            include_context_instruction=True
        )
        logger.info(f"Generating quiz using Knowledge Base + Groq: {len(kb_result['context'])} chars context")
    else:
        # Fallback: Use Groq only (KB failed or empty)
        prompt = base_prompt
        if kb_result["error"]:
            logger.warning(f"Knowledge Base unavailable, using Groq only: {kb_result['error']}")
        else:
            logger.info("No relevant knowledge base content, using Groq only")
    
    try:
        from groq import Groq
        
        client = Groq(api_key=settings.GROQ_API_KEY)
        
        completion = client.chat.completions.create(
            model="llama-3.3-70b-versatile",
            messages=[
                {"role": "system", "content": "You are a quiz generator. Return ONLY valid JSON, no markdown formatting."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000,
        )
        
        response_text = completion.choices[0].message.content.strip()
        
        # Remove markdown code blocks if present
        if response_text.startswith("```"):
            lines = response_text.split("\n")
            response_text = "\n".join(lines[1:-1]) if len(lines) > 2 else response_text
            response_text = response_text.replace("```json", "").replace("```", "").strip()
        
        import json
        quiz_data = json.loads(response_text)
        
        # Generate quiz ID and process questions
        quiz_id = str(uuid.uuid4())
        processed_questions = []
        
        for i, q in enumerate(quiz_data.get("questions", [])[:request.num_questions], 1):
            question_id = str(uuid.uuid4())
            processed_questions.append({
                "question_id": question_id,
                "question_number": i,
                "question": q["question"],
                "options": q["options"],
                "correct_answer": q["correct_answer"],
                "explanation": q.get("explanation", "")
            })
        
        # Store quiz for later validation
        quiz_store[quiz_id] = {
            "subject": request.subject,
            "topic": request.topic,
            "difficulty": request.difficulty,
            "questions": processed_questions,
            "created_at": datetime.now().isoformat()
        }
        
        # Return quiz without answers
        return {
            "quiz_id": quiz_id,
            "subject": request.subject,
            "topic": request.topic,
            "difficulty": request.difficulty,
            "total_questions": len(processed_questions),
            "knowledge_base_used": kb_result["knowledge_base_used"],
            "groq_used": True,
            "fallback_used": not kb_result["knowledge_base_used"],
            "context_length": len(kb_result["context"]) if kb_result["context"] else 0,
            "questions": [
                {
                    "question_id": q["question_id"],
                    "question_number": q["question_number"],
                    "question": q["question"],
                    "options": q["options"]
                }
                for q in processed_questions
            ]
        }
        
    except Exception as e:
        print(f"Quiz Generation Error: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to generate quiz: {str(e)}")

@router.post("/submit")
async def submit_quiz(
    request: QuizSubmitRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Submit quiz answers and get results - saves to DB and syncs to EMS"""
    if request.quiz_id not in quiz_store:
        raise HTTPException(status_code=404, detail="Quiz not found")
    
    quiz_data = quiz_store[request.quiz_id]
    questions = quiz_data["questions"]
    
    correct_count = 0
    wrong_count = 0
    results = []
    user_answers_dict = {}
    
    for q in questions:
        question_id = q["question_id"]
        user_answer = request.answers.get(question_id, "").strip().upper()
        correct_answer = q["correct_answer"]
        
        # Store user answer
        user_answers_dict[question_id] = user_answer if user_answer else "SKIPPED"
        
        # Check if answer is correct
        is_correct = (user_answer == correct_answer)
        
        if is_correct:
            correct_count += 1
        else:
            wrong_count += 1
        
        results.append({
            "question_number": q["question_number"],
            "question": q["question"],
            "user_answer": user_answer if user_answer else "Skipped",
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "explanation": q.get("explanation", "")
        })
    
    score_percentage = round((correct_count / len(questions)) * 100, 2) if questions else 0
    
    # Save test result to database
    test_result = TestResult(
        user_id=current_user.id,
        subject=quiz_data["subject"],
        topic=quiz_data["topic"],
        difficulty=quiz_data["difficulty"],
        num_questions=len(questions),
        questions=[q for q in questions],  # Store all question data
        user_answers=user_answers_dict,
        score=correct_count,
        total_questions=len(questions),
        percentage=score_percentage
    )
    db.add(test_result)
    db.commit()
    db.refresh(test_result)
    
    # Cryptographically chain the review output (Phase 1)
    try:
        from app.services.deterministic_repo import deterministic_repo
        review_data = {
            "test_result_id": test_result.id,
            "correct_count": correct_count,
            "total_questions": len(questions),
            "percentage": score_percentage,
            "results": results
        }
        deterministic_repo.add_review_version(db, submission_id=str(test_result.id), review_json=review_data)
        logger.info(f"Review output version 1 saved and chained for test {test_result.id}")
    except Exception as e:
        logger.error(f"Failed to save chained review version for test {test_result.id}: {e}")
    
    # Sync to EMS asynchronously (don't block response)
    try:
        # Get school_id from user if available (from EMS authentication)
        school_id = getattr(current_user, 'school_id', None)

        ems_sync_result = await ems_sync.sync_test_result(
            gurukul_id=test_result.id,
            student_email=current_user.email,
            school_id=school_id,
            subject=quiz_data["subject"],
            topic=quiz_data["topic"],
            difficulty=quiz_data["difficulty"],
            num_questions=len(questions),
            questions=[q for q in questions],
            user_answers=user_answers_dict,
            score=correct_count,
            total_questions=len(questions),
            percentage=score_percentage
        )
        
        if ems_sync_result:
            test_result.ems_sync_id = ems_sync_result.get("id")
            test_result.synced_to_ems = True
            db.commit()
            logger.info(f"Synced test result {test_result.id} to EMS")
    except Exception as e:
        logger.error(f"Failed to sync test result {test_result.id} to EMS: {str(e)}")
        # Don't fail the request if sync fails
    
    return {
        "quiz_id": request.quiz_id,
        "test_result_id": test_result.id,
        "score": correct_count,
        "total_questions": len(questions),
        "correct_answers": correct_count,
        "wrong_answers": wrong_count,
        "score_percentage": score_percentage,
        "results": results
    }


@router.get("/results")
async def get_user_test_results(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get all test results for the current user"""
    test_results = db.query(TestResult).filter(
        TestResult.user_id == current_user.id
    ).order_by(TestResult.created_at.desc()).all()
    
    return [{
        "id": t.id,
        "subject": t.subject,
        "topic": t.topic,
        "difficulty": t.difficulty,
        "num_questions": t.num_questions,
        "score": t.score,
        "total_questions": t.total_questions,
        "percentage": t.percentage,
        "time_taken": t.time_taken,
        "created_at": t.created_at.isoformat() if t.created_at else None
    } for t in test_results]
