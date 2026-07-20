"""
KSML Processor - Knowledge Structure Markup Language Processor

This service adds semantic labels and educational context annotations
to LM output as part of the Sovereign Polyglot Fusion Layer pipeline.

KSML labels help structure the output for better multilingual processing
and educational context understanding.
"""

import logging
from typing import Dict, Any, List, Optional
import re

logger = logging.getLogger(__name__)


def annotate_with_ksml(text: str, language: str = "en") -> Dict[str, Any]:
    """
    Annotate text with KSML (Knowledge Structure Markup Language) labels
    
    Args:
        text: Input text from LM
        language: Language code of the text
        
    Returns:
        dict: Annotated text with KSML labels and metadata
    """
    try:
        # Extract key information from text
        labels = {
            "language": language,
            "has_questions": _has_questions(text),
            "has_examples": _has_examples(text),
            "has_definitions": _has_definitions(text),
            "educational_level": _detect_educational_level(text),
            "topics": _extract_topics(text),
            "structure": _analyze_structure(text)
        }
        
        # Create KSML-annotated version
        annotated_text = {
            "original": text,
            "ksml_labels": labels,
            "annotated": _add_ksml_tags(text, labels)
        }
        
        logger.debug(f"KSML annotation completed for {language}")
        return annotated_text
        
    except Exception as e:
        logger.error(f"KSML annotation failed: {e}")
        # Return original text with minimal labels on error
        return {
            "original": text,
            "ksml_labels": {"language": language, "error": str(e)},
            "annotated": text
        }


def _has_questions(text: str) -> bool:
    """Check if text contains questions"""
    question_patterns = [
        r'\?',
        r'what\s+is',
        r'how\s+do',
        r'why\s+does',
        r'can\s+you'
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in question_patterns)


def _has_examples(text: str) -> bool:
    """Check if text contains examples"""
    example_indicators = [
        'for example',
        'such as',
        'e.g.',
        'instance',
        'example:'
    ]
    text_lower = text.lower()
    return any(indicator in text_lower for indicator in example_indicators)


def _has_definitions(text: str) -> bool:
    """Check if text contains definitions"""
    definition_patterns = [
        r'is\s+(?:a|an|the)',
        r'means\s+',
        r'refers\s+to',
        r'defined\s+as'
    ]
    text_lower = text.lower()
    return any(re.search(pattern, text_lower) for pattern in definition_patterns)


def _detect_educational_level(text: str) -> str:
    """
    Detect educational level based on text complexity
    
    Returns:
        str: 'beginner', 'intermediate', or 'advanced'
    """
    # Simple heuristic based on sentence length and vocabulary
    sentences = text.split('.')
    avg_sentence_length = sum(len(s.split()) for s in sentences) / max(len(sentences), 1)
    
    if avg_sentence_length < 10:
        return "beginner"
    elif avg_sentence_length < 20:
        return "intermediate"
    else:
        return "advanced"


def _extract_topics(text: str) -> List[str]:
    """Extract potential topics from text (simplified)"""
    # Look for capitalized words that might be topics
    words = text.split()
    topics = []
    
    for i, word in enumerate(words):
        # Check for capitalized words (potential proper nouns/topics)
        if word[0].isupper() and len(word) > 3 and i > 0:
            # Skip if it's start of sentence
            if i == 0 or words[i-1][-1] in '.!?':
                continue
            topics.append(word.strip('.,!?;:'))
    
    return list(set(topics[:5]))  # Return up to 5 unique topics


def _analyze_structure(text: str) -> Dict[str, Any]:
    """Analyze text structure"""
    return {
        "has_headings": bool(re.search(r'^#+\s', text, re.MULTILINE)),
        "has_lists": bool(re.search(r'^[-*•]\s', text, re.MULTILINE)),
        "has_numbered_lists": bool(re.search(r'^\d+\.\s', text, re.MULTILINE)),
        "paragraph_count": len([p for p in text.split('\n\n') if p.strip()]),
        "sentence_count": len([s for s in text.split('.') if s.strip()])
    }


def _add_ksml_tags(text: str, labels: Dict[str, Any]) -> str:
    """
    Add KSML tags to text (simplified version)
    
    In a full implementation, this would add structured markup
    """
    # For now, return original text
    # Full KSML implementation would add XML-like tags
    return text


