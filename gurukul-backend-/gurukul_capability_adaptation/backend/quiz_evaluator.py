"""
Quiz Evaluation Module for Gurukul Learning Platform
Handles quiz submission, scoring, and performance analysis
Source: Backend/subject_generation/quiz_evaluator.py
"""

import json
import re
from typing import List, Dict, Any, Optional
import logging
from datetime import datetime
from difflib import SequenceMatcher

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class QuizEvaluator:
    """Evaluates quiz submissions and provides detailed feedback."""

    def __init__(self):
        self.similarity_threshold = 0.7

    def evaluate_quiz_submission(
        self,
        quiz_data: Dict[str, Any],
        user_answers: Dict[str, Any],
        user_id: str = "anonymous",
    ) -> Dict[str, Any]:
        """Evaluate a complete quiz submission. Returns score_summary (percentage_score, passed, grade), detailed_results, performance_analysis."""
        try:
            logger.info(f"Evaluating quiz submission for user {user_id}")
            questions = quiz_data.get("questions", [])
            total_questions = len(questions)
            total_points = 0
            max_points = quiz_data.get("scoring", {}).get("total_points", total_questions * 10)
            detailed_results = []

            for i, question in enumerate(questions):
                question_id = question.get("question_id", f"q_{i+1}")
                user_answer = user_answers.get(question_id)
                result = self._evaluate_single_question(question, user_answer)
                detailed_results.append(result)
                total_points += result["points_earned"]

            percentage_score = (total_points / max_points) * 100 if max_points > 0 else 0
            passing_score = quiz_data.get("scoring", {}).get("passing_score", max_points * 0.6)
            passed = total_points >= passing_score
            performance_analysis = self._generate_performance_analysis(
                detailed_results, percentage_score, quiz_data.get("subject", ""), quiz_data.get("topic", "")
            )

            return {
                "evaluation_id": f"eval_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
                "user_id": user_id,
                "quiz_id": quiz_data.get("quiz_id", "unknown"),
                "subject": quiz_data.get("subject", ""),
                "topic": quiz_data.get("topic", ""),
                "submitted_at": datetime.now().isoformat(),
                "score_summary": {
                    "total_questions": total_questions,
                    "correct_answers": sum(1 for r in detailed_results if r["is_correct"]),
                    "incorrect_answers": total_questions - sum(1 for r in detailed_results if r["is_correct"]),
                    "total_points": total_points,
                    "max_points": max_points,
                    "percentage_score": round(percentage_score, 2),
                    "passed": passed,
                    "grade": self._calculate_grade(percentage_score),
                },
                "detailed_results": detailed_results,
                "performance_analysis": performance_analysis,
                "completion_data": {
                    "estimated_time": quiz_data.get("estimated_time", 0),
                    "difficulty": quiz_data.get("difficulty", "medium"),
                },
            }
        except Exception as e:
            logger.error(f"Error evaluating quiz submission: {e}")
            return self._generate_error_result(user_id, str(e))

    def _evaluate_single_question(self, question: Dict[str, Any], user_answer: Any) -> Dict[str, Any]:
        question_type = question.get("type", "multiple_choice")
        question_id = question.get("question_id", "unknown")
        max_points = question.get("points", 10)
        if question_type == "multiple_choice":
            return self._evaluate_multiple_choice(question, user_answer, max_points)
        elif question_type == "true_false":
            return self._evaluate_true_false(question, user_answer, max_points)
        elif question_type == "fill_in_blank":
            return self._evaluate_fill_in_blank(question, user_answer, max_points)
        elif question_type == "short_answer":
            return self._evaluate_short_answer(question, user_answer, max_points)
        return self._generate_question_error_result(question_id, "Unknown question type", max_points)

    def _evaluate_multiple_choice(self, question: Dict[str, Any], user_answer: Any, max_points: int) -> Dict[str, Any]:
        correct_answer = question.get("correct_answer", 0)
        is_correct = user_answer == correct_answer
        return {
            "question_id": question.get("question_id"),
            "question_type": "multiple_choice",
            "question_text": question.get("question", question.get("question_text", "")),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "points_earned": max_points if is_correct else 0,
            "max_points": max_points,
            "feedback": self._generate_feedback(question, is_correct),
            "explanation": question.get("explanation", ""),
        }

    def _evaluate_true_false(self, question: Dict[str, Any], user_answer: Any, max_points: int) -> Dict[str, Any]:
        correct_answer = question.get("correct_answer", True)
        is_correct = user_answer == correct_answer
        return {
            "question_id": question.get("question_id"),
            "question_type": "true_false",
            "question_text": question.get("question", question.get("question_text", "")),
            "user_answer": user_answer,
            "correct_answer": correct_answer,
            "is_correct": is_correct,
            "points_earned": max_points if is_correct else 0,
            "max_points": max_points,
            "feedback": self._generate_feedback(question, is_correct),
            "explanation": question.get("explanation", ""),
        }

    def _evaluate_fill_in_blank(self, question: Dict[str, Any], user_answer: Any, max_points: int) -> Dict[str, Any]:
        correct_answer = question.get("correct_answer", "").strip().lower()
        user_answer_clean = str(user_answer).strip().lower() if user_answer else ""
        is_exact_match = user_answer_clean == correct_answer
        similarity = SequenceMatcher(None, user_answer_clean, correct_answer).ratio()
        is_similar = similarity >= self.similarity_threshold
        is_correct = is_exact_match or is_similar
        points_earned = max_points if is_exact_match else (max_points * 0.8 if is_similar else 0)
        return {
            "question_id": question.get("question_id"),
            "question_type": "fill_in_blank",
            "question_text": question.get("question", question.get("question_text", "")),
            "user_answer": user_answer,
            "correct_answer": question.get("correct_answer"),
            "is_correct": is_correct,
            "points_earned": int(points_earned),
            "max_points": max_points,
            "similarity_score": round(similarity, 2),
            "feedback": self._generate_feedback(question, is_correct),
            "explanation": question.get("explanation", ""),
        }

    def _evaluate_short_answer(self, question: Dict[str, Any], user_answer: Any, max_points: int) -> Dict[str, Any]:
        sample_answer = question.get("sample_answer", "").strip().lower()
        user_answer_clean = str(user_answer).strip().lower() if user_answer else ""
        if not user_answer_clean:
            similarity, is_correct, points_earned = 0.0, False, 0
        else:
            similarity = SequenceMatcher(None, user_answer_clean, sample_answer).ratio()
            key_terms = self._extract_key_terms(sample_answer)
            term_matches = sum(1 for term in key_terms if term in user_answer_clean)
            term_score = term_matches / len(key_terms) if key_terms else 0
            combined_score = (similarity * 0.6) + (term_score * 0.4)
            is_correct = combined_score >= 0.5
            points_earned = int(max_points * combined_score)
        return {
            "question_id": question.get("question_id"),
            "question_type": "short_answer",
            "question_text": question.get("question", question.get("question_text", "")),
            "user_answer": user_answer,
            "sample_answer": question.get("sample_answer"),
            "is_correct": is_correct,
            "points_earned": points_earned,
            "max_points": max_points,
            "similarity_score": round(similarity, 2),
            "feedback": self._generate_feedback(question, is_correct),
            "explanation": question.get("explanation", ""),
        }

    def _extract_key_terms(self, text: str) -> List[str]:
        common_words = {"the", "a", "an", "and", "or", "but", "in", "on", "at", "to", "for", "of", "with", "by", "is", "are", "was", "were", "be", "been", "have", "has", "had", "do", "does", "did", "will", "would", "could", "should"}
        words = re.findall(r"\b\w+\b", text.lower())
        return list(set(word for word in words if word not in common_words and len(word) > 2))

    def _generate_feedback(self, question: Dict[str, Any], is_correct: bool) -> str:
        if is_correct:
            return "Excellent! Your answer is correct."
        return f"Not quite right. {question.get('explanation', 'Please review the material and try again.')}"

    def _calculate_grade(self, percentage: float) -> str:
        if percentage >= 90: return "A"
        if percentage >= 80: return "B"
        if percentage >= 70: return "C"
        if percentage >= 60: return "D"
        return "F"

    def _generate_performance_analysis(self, results: List[Dict], percentage: float, subject: str, topic: str) -> Dict[str, Any]:
        type_performance = {}
        for result in results:
            q_type = result["question_type"]
            if q_type not in type_performance:
                type_performance[q_type] = {"correct": 0, "total": 0}
            type_performance[q_type]["total"] += 1
            if result["is_correct"]:
                type_performance[q_type]["correct"] += 1
        recommendations = []
        if percentage < 60:
            recommendations.append(f"Consider reviewing the fundamental concepts of {topic} in {subject}")
            recommendations.append("Practice more questions to strengthen your understanding")
        elif percentage < 80:
            recommendations.append("Good progress! Focus on the areas where you missed questions")
            recommendations.append("Try more advanced practice questions")
        else:
            recommendations.append("Excellent performance! Consider exploring more advanced topics.")
        return {
            "overall_performance": "Excellent" if percentage >= 80 else "Good" if percentage >= 60 else "Needs Improvement",
            "strengths": [f"Strong performance in {q_type}" for q_type, perf in type_performance.items() if perf["total"] and perf["correct"] / perf["total"] >= 0.8],
            "areas_for_improvement": [f"Review {q_type} questions" for q_type, perf in type_performance.items() if perf["total"] and perf["correct"] / perf["total"] < 0.6],
            "recommendations": recommendations,
            "type_performance": type_performance,
        }

    def _generate_question_error_result(self, question_id: str, error_msg: str, max_points: int) -> Dict[str, Any]:
        return {"question_id": question_id, "question_type": "error", "error": error_msg, "is_correct": False, "points_earned": 0, "max_points": max_points, "feedback": "There was an error evaluating this question."}

    def _generate_error_result(self, user_id: str, error_msg: str) -> Dict[str, Any]:
        return {
            "evaluation_id": f"error_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            "user_id": user_id,
            "error": error_msg,
            "submitted_at": datetime.now().isoformat(),
            "score_summary": {"total_questions": 0, "correct_answers": 0, "total_points": 0, "max_points": 0, "percentage_score": 0, "passed": False, "grade": "F"},
        }
