"""
Evaluation Engine Service

Runs cross-language evaluation using BLEU, ROUGE, and COMET-lite metrics.
Focused on Arabic language evaluation for the Sovereign Fusion Layer.

Loads test cases from eval_cards and generates accuracy reports.
"""

import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from app.services.metrics import (
    calculate_bleu,
    calculate_rouge,
    calculate_comet_lite,
    generate_evaluation_report
)

logger = logging.getLogger(__name__)


def _get_eval_card_path(language: str) -> Path:
    """Get path to evaluation card JSON file"""
    return Path(__file__).parent.parent.parent / "eval_cards" / f"{language}.json"


def load_eval_card(language: str) -> Dict[str, Any]:
    """
    Load evaluation test cases from eval card file
    
    Args:
        language: Language code (e.g., 'ar' for Arabic)
        
    Returns:
        dict: Evaluation card data with test cases
        
    Raises:
        FileNotFoundError: If eval card doesn't exist
    """
    eval_card_path = _get_eval_card_path(language)
    
    if not eval_card_path.exists():
        raise FileNotFoundError(
            f"Evaluation card not found for language: {language} at {eval_card_path}"
        )
    
    with open(eval_card_path, 'r', encoding='utf-8') as f:
        eval_card = json.load(f)
    
    logger.info(f"Loaded eval card for {language}: {len(eval_card.get('test_cases', []))} test cases")
    return eval_card


def run_evaluation(
    language: str,
    test_cases: Optional[List[Dict[str, Any]]] = None,
    hypothesis_generator: Optional[callable] = None
) -> List[Dict[str, Any]]:
    """
    Run evaluation on test cases
    
    Args:
        language: Language code to evaluate
        test_cases: Optional list of test cases (if None, loads from eval card)
        hypothesis_generator: Optional function to generate hypotheses
                            (if None, expects test cases to have 'hypothesis' field)
        
    Returns:
        list: Evaluation results for each test case
    """
    # Load test cases if not provided
    if test_cases is None:
        eval_card = load_eval_card(language)
        test_cases = eval_card.get('test_cases', [])
    
    results = []
    
    for test_case in test_cases:
        test_id = test_case.get('id', 'unknown')
        source = test_case.get('source', '')
        reference = test_case.get('reference', '')
        
        # Get hypothesis (either from generator or test case)
        if hypothesis_generator:
            hypothesis = hypothesis_generator(source, test_case)
        else:
            hypothesis = test_case.get('hypothesis', '')
        
        if not hypothesis:
            logger.warning(f"No hypothesis for test case {test_id}, skipping")
            continue
        
        # Calculate all metrics
        bleu_result = calculate_bleu(reference, hypothesis)
        rouge_result = calculate_rouge(reference, hypothesis)
        comet_result = calculate_comet_lite(source, reference, hypothesis)
        
        result = {
            "test_id": test_id,
            "source": source,
            "reference": reference,
            "hypothesis": hypothesis,
            "metrics": {
                "bleu": bleu_result,
                "rouge": rouge_result,
                "comet": comet_result
            },
            "category": test_case.get('category', 'unknown'),
            "difficulty": test_case.get('difficulty', 'unknown')
        }
        
        results.append(result)
        logger.debug(f"Evaluated test case {test_id}")
    
    return results


def generate_accuracy_report(language: str, results: Optional[List[Dict[str, Any]]] = None) -> Dict[str, Any]:
    """
    Generate accuracy report for a language
    
    Args:
        language: Language code
        results: Optional pre-computed results (if None, runs evaluation)
        
    Returns:
        dict: Comprehensive accuracy report
    """
    if results is None:
        results = run_evaluation(language)
    
    # Generate report using metrics service
    report = generate_evaluation_report(results, language)
    
    # Add additional statistics
    report["statistics"] = {
        "total_cases": len(results),
        "cases_by_category": _count_by_category(results),
        "cases_by_difficulty": _count_by_difficulty(results),
        "average_scores_by_category": _average_scores_by_category(results),
        "average_scores_by_difficulty": _average_scores_by_difficulty(results)
    }
    
    return report


def _count_by_category(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count test cases by category"""
    categories = {}
    for result in results:
        category = result.get('category', 'unknown')
        categories[category] = categories.get(category, 0) + 1
    return categories


def _count_by_difficulty(results: List[Dict[str, Any]]) -> Dict[str, int]:
    """Count test cases by difficulty"""
    difficulties = {}
    for result in results:
        difficulty = result.get('difficulty', 'unknown')
        difficulties[difficulty] = difficulties.get(difficulty, 0) + 1
    return difficulties


def _average_scores_by_category(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Calculate average scores grouped by category"""
    category_scores = {}
    
    for result in results:
        category = result.get('category', 'unknown')
        if category not in category_scores:
            category_scores[category] = {
                "bleu": [],
                "rouge_1": [],
                "rouge_2": [],
                "rouge_l": [],
                "comet_lite": []
            }
        
        metrics = result.get('metrics', {})
        category_scores[category]["bleu"].append(metrics.get('bleu', {}).get('bleu', 0.0))
        category_scores[category]["rouge_1"].append(metrics.get('rouge', {}).get('rouge_1', 0.0))
        category_scores[category]["rouge_2"].append(metrics.get('rouge', {}).get('rouge_2', 0.0))
        category_scores[category]["rouge_l"].append(metrics.get('rouge', {}).get('rouge_l', 0.0))
        category_scores[category]["comet_lite"].append(metrics.get('comet', {}).get('comet_lite', 0.0))
    
    # Calculate averages
    averages = {}
    for category, scores in category_scores.items():
        averages[category] = {
            "bleu": round(sum(scores["bleu"]) / len(scores["bleu"]), 4) if scores["bleu"] else 0.0,
            "rouge_1": round(sum(scores["rouge_1"]) / len(scores["rouge_1"]), 4) if scores["rouge_1"] else 0.0,
            "rouge_2": round(sum(scores["rouge_2"]) / len(scores["rouge_2"]), 4) if scores["rouge_2"] else 0.0,
            "rouge_l": round(sum(scores["rouge_l"]) / len(scores["rouge_l"]), 4) if scores["rouge_l"] else 0.0,
            "comet_lite": round(sum(scores["comet_lite"]) / len(scores["comet_lite"]), 4) if scores["comet_lite"] else 0.0
        }
    
    return averages


def _average_scores_by_difficulty(results: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    """Calculate average scores grouped by difficulty"""
    difficulty_scores = {}
    
    for result in results:
        difficulty = result.get('difficulty', 'unknown')
        if difficulty not in difficulty_scores:
            difficulty_scores[difficulty] = {
                "bleu": [],
                "rouge_1": [],
                "rouge_2": [],
                "rouge_l": [],
                "comet_lite": []
            }
        
        metrics = result.get('metrics', {})
        difficulty_scores[difficulty]["bleu"].append(metrics.get('bleu', {}).get('bleu', 0.0))
        difficulty_scores[difficulty]["rouge_1"].append(metrics.get('rouge', {}).get('rouge_1', 0.0))
        difficulty_scores[difficulty]["rouge_2"].append(metrics.get('rouge', {}).get('rouge_2', 0.0))
        difficulty_scores[difficulty]["rouge_l"].append(metrics.get('rouge', {}).get('rouge_l', 0.0))
        difficulty_scores[difficulty]["comet_lite"].append(metrics.get('comet', {}).get('comet_lite', 0.0))
    
    # Calculate averages
    averages = {}
    for difficulty, scores in difficulty_scores.items():
        averages[difficulty] = {
            "bleu": round(sum(scores["bleu"]) / len(scores["bleu"]), 4) if scores["bleu"] else 0.0,
            "rouge_1": round(sum(scores["rouge_1"]) / len(scores["rouge_1"]), 4) if scores["rouge_1"] else 0.0,
            "rouge_2": round(sum(scores["rouge_2"]) / len(scores["rouge_2"]), 4) if scores["rouge_2"] else 0.0,
            "rouge_l": round(sum(scores["rouge_l"]) / len(scores["rouge_l"]), 4) if scores["rouge_l"] else 0.0,
            "comet_lite": round(sum(scores["comet_lite"]) / len(scores["comet_lite"]), 4) if scores["comet_lite"] else 0.0
        }
    
    return averages

