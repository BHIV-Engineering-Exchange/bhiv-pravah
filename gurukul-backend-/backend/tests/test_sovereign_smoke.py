"""
Smoke Tests for Sovereign Fusion Layer

These tests verify basic functionality of the Sovereign Fusion Layer
without requiring full model loading or database setup.

Run with: pytest tests/test_sovereign_smoke.py -v
"""

import pytest
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.ksml_processor import annotate_with_ksml
from app.services.adapter_registry import (
    load_registry,
    get_adapter_for_language,
    validate_adapter
)
from app.services.prosody_mapper import (
    generate_prosody_hint,
    validate_prosody_hint,
    get_available_tones
)
from app.services.metrics import (
    calculate_bleu,
    calculate_rouge,
    calculate_comet_lite
)
from app.services.evaluation_engine import load_eval_card


class TestKSMLProcessor:
    """Test KSML processor functionality"""
    
    def test_annotate_basic(self):
        """Test basic KSML annotation"""
        text = "What is mathematics?"
        result = annotate_with_ksml(text, language="en")
        
        assert "ksml_labels" in result
        assert "annotated" in result
        assert result["ksml_labels"]["language"] == "en"
        assert result["ksml_labels"]["has_questions"] == True
    
    def test_annotate_arabic(self):
        """Test KSML annotation with Arabic text"""
        text = "ما هي الرياضيات؟"
        result = annotate_with_ksml(text, language="ar")
        
        assert result["ksml_labels"]["language"] == "ar"
        assert "annotated" in result


class TestAdapterRegistry:
    """Test adapter registry functionality"""
    
    def test_load_registry(self):
        """Test loading adapter registry"""
        registry = load_registry()
        
        assert "version" in registry
        assert "adapters" in registry
        assert isinstance(registry["adapters"], list)
    
    def test_get_arabic_adapter(self):
        """Test getting Arabic adapter"""
        adapter = get_adapter_for_language("ar")
        
        assert adapter is not None
        assert adapter["lang"] == "ar"
        assert adapter["language_name"] == "Arabic"
    
    def test_get_nonexistent_adapter(self):
        """Test getting adapter for unsupported language"""
        adapter = get_adapter_for_language("xyz")
        
        assert adapter is None
    
    def test_validate_adapter_path(self):
        """Test adapter path validation"""
        # Test with non-existent path (should return False)
        result = validate_adapter("nonexistent/path.bin")
        assert result is False


class TestProsodyMapper:
    """Test prosody mapper functionality"""
    
    def test_generate_prosody_hint(self):
        """Test prosody hint generation"""
        prosody = generate_prosody_hint(
            text="Hello",
            lang="ar",
            tone="educational"
        )
        
        assert prosody is not None
        assert "prosody_hint" in prosody
        assert prosody["prosody_hint"] == "educational_ar"
        assert "pitch" in prosody
        assert "speed" in prosody
    
    def test_validate_prosody_hint(self):
        """Test prosody hint validation"""
        prosody = {
            "prosody_hint": "educational_ar",
            "pitch": 0.55,
            "speed": 0.95,
            "emphasis": 0.4
        }
        
        result = validate_prosody_hint(prosody)
        assert result is True
    
    def test_get_available_tones(self):
        """Test getting available tones"""
        tones = get_available_tones("ar")
        
        assert isinstance(tones, list)
        assert "neutral" in tones
        assert "educational" in tones


class TestMetrics:
    """Test evaluation metrics"""
    
    def test_bleu_score(self):
        """Test BLEU score calculation"""
        reference = "ما هي الرياضيات؟"
        hypothesis = "ما هي الرياضيات؟"
        
        result = calculate_bleu(reference, hypothesis)
        
        assert "bleu_score" in result
        assert result["bleu_score"] > 0.0
    
    def test_rouge_score(self):
        """Test ROUGE score calculation"""
        reference = "Mathematics is the study of numbers and shapes."
        hypothesis = "Mathematics studies numbers and shapes."
        
        result = calculate_rouge(reference, hypothesis)
        
        assert "rouge_1" in result
        assert "rouge_2" in result
        assert "rouge_l" in result
    
    def test_comet_lite(self):
        """Test COMET-lite score calculation"""
        reference = "Hello world"
        hypothesis = "Hello world"
        
        result = calculate_comet_lite(reference, hypothesis)
        
        assert "comet_score" in result
        assert 0.0 <= result["comet_score"] <= 1.0


class TestEvaluationEngine:
    """Test evaluation engine functionality"""
    
    def test_load_eval_card(self):
        """Test loading evaluation card"""
        card = load_eval_card("ar")
        
        assert card is not None
        assert "language" in card
        assert card["language"] == "ar"
        assert "test_cases" in card
        assert len(card["test_cases"]) > 0
    
    def test_eval_card_structure(self):
        """Test evaluation card structure"""
        card = load_eval_card("ar")
        
        test_case = card["test_cases"][0]
        assert "id" in test_case
        assert "source" in test_case
        assert "reference" in test_case


class TestIntegration:
    """Integration tests for full pipeline"""
    
    def test_pipeline_components_exist(self):
        """Test that all pipeline components can be imported"""
        from app.services.sovereign_lm_core import is_model_loaded
        from app.services.rl_loop import process_lm_output
        from app.services.reward_manager import get_unified_rewards
        
        # Just verify imports work
        assert callable(is_model_loaded)
        assert callable(process_lm_output)
        assert callable(get_unified_rewards)
    
    def test_schema_validation(self):
        """Test that schemas are properly defined"""
        from app.schemas.sovereign import (
            SovereignInferRequest,
            SovereignInferResponse,
            PipelineStage
        )
        
        # Test request schema
        request = SovereignInferRequest(
            text="Test",
            lang="en",
            target_lang="ar",
            tone="neutral"
        )
        assert request.text == "Test"
        assert request.lang == "en"
        
        # Test response schema
        response = SovereignInferResponse(
            output="Output",
            target_lang="ar",
            pipeline_stages=[],
            metadata={}
        )
        assert response.output == "Output"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])

