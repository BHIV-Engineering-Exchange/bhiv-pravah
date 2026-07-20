"""
Evaluation Metrics Service

Implements BLEU, ROUGE, and COMET-lite metrics for evaluating
translation quality and text generation accuracy.

Focused on Arabic language evaluation for the Sovereign Fusion Layer.
"""

import logging
from typing import List, Dict, Any, Optional
import re

logger = logging.getLogger(__name__)


def calculate_bleu(reference: str, hypothesis: str) -> Dict[str, float]:
    """
    Calculate BLEU score for translation evaluation
    
    BLEU (Bilingual Evaluation Understudy) measures n-gram precision
    between reference and hypothesis translations.
    
    Args:
        reference: Reference (ground truth) text
        hypothesis: Generated/hypothesis text to evaluate
        
    Returns:
        dict: BLEU score and breakdown by n-gram
    """
    try:
        if reference == hypothesis:
            ref_tokens = _tokenize(reference)
            return {
                "bleu": 1.0,
                "bleu_score": 1.0,
                "precision_1": 1.0,
                "precision_2": 1.0,
                "precision_3": 1.0,
                "precision_4": 1.0,
                "brevity_penalty": 1.0,
                "reference_length": len(ref_tokens),
                "hypothesis_length": len(ref_tokens)
            }
            
        # Simple BLEU implementation (for production, use sacrebleu library)
        ref_tokens = _tokenize(reference)
        hyp_tokens = _tokenize(hypothesis)
        
        if len(hyp_tokens) == 0:
            return {"bleu": 0.0, "precision_1": 0.0, "precision_2": 0.0, "precision_3": 0.0, "precision_4": 0.0}
        
        # Calculate precision for 1-4 grams
        precisions = {}
        for n in range(1, 5):
            ref_ngrams = _get_ngrams(ref_tokens, n)
            hyp_ngrams = _get_ngrams(hyp_tokens, n)
            
            if len(hyp_ngrams) == 0:
                precisions[f"precision_{n}"] = 0.0
            else:
                matches = sum(1 for ngram in hyp_ngrams if ngram in ref_ngrams)
                precisions[f"precision_{n}"] = matches / len(hyp_ngrams)
        
        # Calculate brevity penalty
        ref_len = len(ref_tokens)
        hyp_len = len(hyp_tokens)
        brevity_penalty = min(1.0, ref_len / hyp_len) if hyp_len > 0 else 0.0
        
        # Calculate BLEU (geometric mean of precisions * brevity penalty)
        precision_product = 1.0
        for n in range(1, 5):
            precision_product *= precisions[f"precision_{n}"]
        
        bleu = brevity_penalty * (precision_product ** 0.25)
        
        return {
            "bleu": round(bleu, 4),
            "bleu_score": round(bleu, 4),
            **precisions,
            "brevity_penalty": round(brevity_penalty, 4),
            "reference_length": ref_len,
            "hypothesis_length": hyp_len
        }
        
    except Exception as e:
        logger.error(f"BLEU calculation failed: {e}")
        return {"bleu": 0.0, "bleu_score": 0.0, "error": str(e)}


def calculate_rouge(reference: str, hypothesis: str) -> Dict[str, float]:
    """
    Calculate ROUGE scores (ROUGE-1, ROUGE-2, ROUGE-L)
    
    ROUGE (Recall-Oriented Understudy for Gisting Evaluation) measures
    overlap of n-grams and longest common subsequence.
    
    Args:
        reference: Reference text
        hypothesis: Hypothesis text to evaluate
        
    Returns:
        dict: ROUGE-1, ROUGE-2, and ROUGE-L scores
    """
    try:
        ref_tokens = _tokenize(reference)
        hyp_tokens = _tokenize(hypothesis)
        
        if len(ref_tokens) == 0 or len(hyp_tokens) == 0:
            return {
                "rouge_1": 0.0,
                "rouge_2": 0.0,
                "rouge_l": 0.0
            }
        
        # ROUGE-1 (unigram overlap)
        ref_unigrams = set(_get_ngrams(ref_tokens, 1))
        hyp_unigrams = set(_get_ngrams(hyp_tokens, 1))
        overlap_1 = len(ref_unigrams & hyp_unigrams)
        rouge_1_precision = overlap_1 / len(hyp_unigrams) if len(hyp_unigrams) > 0 else 0.0
        rouge_1_recall = overlap_1 / len(ref_unigrams) if len(ref_unigrams) > 0 else 0.0
        rouge_1_f1 = 2 * (rouge_1_precision * rouge_1_recall) / (rouge_1_precision + rouge_1_recall) if (rouge_1_precision + rouge_1_recall) > 0 else 0.0
        
        # ROUGE-2 (bigram overlap)
        ref_bigrams = set(_get_ngrams(ref_tokens, 2))
        hyp_bigrams = set(_get_ngrams(hyp_tokens, 2))
        overlap_2 = len(ref_bigrams & hyp_bigrams)
        rouge_2_precision = overlap_2 / len(hyp_bigrams) if len(hyp_bigrams) > 0 else 0.0
        rouge_2_recall = overlap_2 / len(ref_bigrams) if len(ref_bigrams) > 0 else 0.0
        rouge_2_f1 = 2 * (rouge_2_precision * rouge_2_recall) / (rouge_2_precision + rouge_2_recall) if (rouge_2_precision + rouge_2_recall) > 0 else 0.0
        
        # ROUGE-L (longest common subsequence)
        lcs_length = _lcs_length(ref_tokens, hyp_tokens)
        rouge_l_precision = lcs_length / len(hyp_tokens) if len(hyp_tokens) > 0 else 0.0
        rouge_l_recall = lcs_length / len(ref_tokens) if len(ref_tokens) > 0 else 0.0
        rouge_l_f1 = 2 * (rouge_l_precision * rouge_l_recall) / (rouge_l_precision + rouge_l_recall) if (rouge_l_precision + rouge_l_recall) > 0 else 0.0
        
        return {
            "rouge_1": round(rouge_1_f1, 4),
            "rouge_1_precision": round(rouge_1_precision, 4),
            "rouge_1_recall": round(rouge_1_recall, 4),
            "rouge_2": round(rouge_2_f1, 4),
            "rouge_2_precision": round(rouge_2_precision, 4),
            "rouge_2_recall": round(rouge_2_recall, 4),
            "rouge_l": round(rouge_l_f1, 4),
            "rouge_l_precision": round(rouge_l_precision, 4),
            "rouge_l_recall": round(rouge_l_recall, 4)
        }
        
    except Exception as e:
        logger.error(f"ROUGE calculation failed: {e}")
        return {"rouge_1": 0.0, "rouge_2": 0.0, "rouge_l": 0.0, "error": str(e)}


def calculate_comet_lite(source_or_ref: str, reference_or_hyp: str, hypothesis: Optional[str] = None) -> Dict[str, float]:
    """
    Calculate COMET-lite score (simplified version)
    
    COMET (Crosslingual Optimized Metric for Evaluation with Translation)
    uses neural networks to evaluate translation quality.
    
    This is a simplified version. For production, use the full COMET library.
    
    Args:
        source_or_ref: Source text (original) or Reference translation
        reference_or_hyp: Reference translation or Hypothesis translation
        hypothesis: Hypothesis translation to evaluate (optional)
        
    Returns:
        dict: COMET-lite score and metadata
    """
    try:
        if hypothesis is None:
            # Called as calculate_comet_lite(reference, hypothesis)
            reference = source_or_ref
            hypothesis = reference_or_hyp
            source = ""
        else:
            # Called as calculate_comet_lite(source, reference, hypothesis)
            source = source_or_ref
            reference = reference_or_hyp
            
        # Simplified COMET-lite: combination of semantic similarity metrics
        # In production, this would use a neural model
        
        # Calculate semantic overlap (simplified)
        ref_tokens = set(_tokenize(reference))
        hyp_tokens = set(_tokenize(hypothesis))
        
        overlap = len(ref_tokens & hyp_tokens)
        total_unique = len(ref_tokens | hyp_tokens)
        
        semantic_similarity = overlap / total_unique if total_unique > 0 else 0.0
        
        # Combine with length ratio
        ref_len = len(_tokenize(reference))
        hyp_len = len(_tokenize(hypothesis))
        length_ratio = min(hyp_len / ref_len, ref_len / hyp_len) if ref_len > 0 and hyp_len > 0 else 0.0
        
        # Simple COMET-lite score (weighted combination)
        comet_score = 0.7 * semantic_similarity + 0.3 * length_ratio
        
        return {
            "comet_lite": round(comet_score, 4),
            "comet_score": round(comet_score, 4),
            "semantic_similarity": round(semantic_similarity, 4),
            "length_ratio": round(length_ratio, 4)
        }
        
    except Exception as e:
        logger.error(f"COMET-lite calculation failed: {e}")
        return {"comet_lite": 0.0, "comet_score": 0.0, "error": str(e)}


def _tokenize(text: str) -> List[str]:
    """Tokenize text (handles Arabic and English)"""
    # Simple tokenization - split by whitespace and punctuation
    # For production, use proper tokenizers (e.g., for Arabic: camel-tools)
    tokens = re.findall(r'\S+', text)
    return tokens


def _get_ngrams(tokens: List[str], n: int) -> List[tuple]:
    """Get n-grams from token list"""
    if n > len(tokens):
        return []
    return [tuple(tokens[i:i+n]) for i in range(len(tokens) - n + 1)]


def _lcs_length(seq1: List[str], seq2: List[str]) -> int:
    """Calculate length of longest common subsequence"""
    m, n = len(seq1), len(seq2)
    dp = [[0] * (n + 1) for _ in range(m + 1)]
    
    for i in range(1, m + 1):
        for j in range(1, n + 1):
            if seq1[i-1] == seq2[j-1]:
                dp[i][j] = dp[i-1][j-1] + 1
            else:
                dp[i][j] = max(dp[i-1][j], dp[i][j-1])
    
    return dp[m][n]


def generate_evaluation_report(results: List[Dict[str, Any]], language: str = "ar") -> Dict[str, Any]:
    """
    Generate comprehensive evaluation report from metric results
    
    Args:
        results: List of evaluation results (each with metrics)
        language: Language code being evaluated
        
    Returns:
        dict: Summary report with averages and statistics
    """
    if not results:
        return {"error": "No results to generate report from"}
    
    # Calculate averages
    avg_bleu = sum(r.get("bleu", {}).get("bleu", 0.0) for r in results) / len(results)
    avg_rouge_1 = sum(r.get("rouge", {}).get("rouge_1", 0.0) for r in results) / len(results)
    avg_rouge_2 = sum(r.get("rouge", {}).get("rouge_2", 0.0) for r in results) / len(results)
    avg_rouge_l = sum(r.get("rouge", {}).get("rouge_l", 0.0) for r in results) / len(results)
    avg_comet = sum(r.get("comet", {}).get("comet_lite", 0.0) for r in results) / len(results)
    
    return {
        "language": language,
        "total_test_cases": len(results),
        "averages": {
            "bleu": round(avg_bleu, 4),
            "rouge_1": round(avg_rouge_1, 4),
            "rouge_2": round(avg_rouge_2, 4),
            "rouge_l": round(avg_rouge_l, 4),
            "comet_lite": round(avg_comet, 4)
        },
        "overall_score": round((avg_bleu + avg_rouge_1 + avg_rouge_2 + avg_rouge_l + avg_comet) / 5, 4),
        "results": results
    }

