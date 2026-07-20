"""
Sovereign Fusion Layer Router

Unified inference endpoint that chains:
Your Model → KSML → RL → Adapter → Vaani-prep

This is the main entry point for the Sovereign Polyglot Fusion Layer.
"""

import time
import logging
import uuid
from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from app.schemas.sovereign import SovereignInferRequest, SovereignInferResponse, PipelineStage
from app.services.sovereign_lm_core import generate as lm_generate
from app.services.ksml_processor import annotate_with_ksml
from app.services.adapter_registry import get_adapter_for_language, validate_adapter
from app.services.prosody_mapper import generate_prosody_hint, validate_prosody_hint
from app.services.rl_loop import (
    process_lm_output,
    process_ksml_labels,
    process_vaani_feedback,
    merge_episodes
)
from app.core.database import get_db

logger = logging.getLogger(__name__)

router = APIRouter()


@router.post("/infer", response_model=SovereignInferResponse)
async def sovereign_infer(
    request: SovereignInferRequest,
    db: Session = Depends(get_db)
):
    """
    Unified inference endpoint for multilingual processing
    
    Pipeline:
    1. LM Core (Your fine-tuned model) - processes input text
    2. KSML Processor - adds semantic labels and educational context
    3. RL Processing - (placeholder for Day 5)
    4. Adapter Selection - (placeholder for Day 2)
    5. Vaani Preparation - prepares for TTS (placeholder for Day 4)
    
    Args:
        request: SovereignInferRequest with text, lang, target_lang, tone
        
    Returns:
        SovereignInferResponse with processed output and pipeline details
    """
    pipeline_stages = []
    current_output = request.text
    target_lang = request.target_lang or request.lang
    
    # Generate episode ID for RL tracking
    episode_id = f"ep_{uuid.uuid4().hex[:12]}"
    episode_data = {
        "episode_id": episode_id,
        "source_text": request.text,
        "target_lang": target_lang,
        "tone": request.tone
    }
    rewards = []
    
    try:
        # Stage 1: LM Core Processing
        stage_start = time.time()
        try:
            lm_output = await lm_generate(
                prompt=request.text,
                system_prompt=f"You are an educational assistant. Respond in {target_lang}.",
                max_tokens=512,
                temperature=0.7
            )
            current_output = lm_output
            episode_data["lm_output"] = lm_output
            
            # Process LM output for RL reward
            try:
                lm_reward = process_lm_output(lm_output, request.text, request.lang, db)
                rewards.append(lm_reward)
            except Exception as e:
                logger.warning(f"RL reward processing for LM failed: {e}")
            
            pipeline_stages.append(PipelineStage(
                stage_name="lm_core",
                status="success",
                output=lm_output[:100] + "..." if len(lm_output) > 100 else lm_output,
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        except Exception as e:
            logger.error(f"LM Core failed: {e}")
            pipeline_stages.append(PipelineStage(
                stage_name="lm_core",
                status="error",
                metadata={"error": str(e)},
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
            # Continue with original text if LM fails
            current_output = request.text
        
        # Stage 2: KSML Processing
        stage_start = time.time()
        try:
            ksml_result = annotate_with_ksml(current_output, language=request.lang)
            current_output = ksml_result.get("annotated", current_output)
            episode_data["ksml_labels"] = ksml_result.get("ksml_labels", {})
            
            # Process KSML labels for RL reward
            try:
                ksml_reward = process_ksml_labels(ksml_result, request.lang, db)
                rewards.append(ksml_reward)
            except Exception as e:
                logger.warning(f"RL reward processing for KSML failed: {e}")
            
            pipeline_stages.append(PipelineStage(
                stage_name="ksml",
                status="success",
                metadata=ksml_result.get("ksml_labels", {}),
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        except Exception as e:
            logger.error(f"KSML processing failed: {e}")
            pipeline_stages.append(PipelineStage(
                stage_name="ksml",
                status="error",
                metadata={"error": str(e)},
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        
        # Stage 3: RL Processing
        stage_start = time.time()
        try:
            # Merge all rewards into unified episode
            merged_episode_id = merge_episodes(episode_data, rewards, db)
            pipeline_stages.append(PipelineStage(
                stage_name="rl_processing",
                status="success",
                metadata={
                    "episode_id": merged_episode_id,
                    "rewards_count": len(rewards),
                    "sources": [r.get("source") for r in rewards]
                },
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        except Exception as e:
            logger.error(f"RL processing failed: {e}")
            pipeline_stages.append(PipelineStage(
                stage_name="rl_processing",
                status="error",
                metadata={"error": str(e)},
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        
        # Stage 4: Adapter Selection
        stage_start = time.time()
        try:
            adapter = get_adapter_for_language(target_lang)
            if adapter:
                # Validate adapter file exists
                adapter_valid = validate_adapter(adapter.get('path', ''))
                pipeline_stages.append(PipelineStage(
                    stage_name="adapter_selection",
                    status="success" if adapter_valid else "warning",
                    metadata={
                        "adapter_lang": adapter.get('lang'),
                        "adapter_version": adapter.get('version'),
                        "adapter_validated": adapter_valid,
                        "rtl": adapter.get('rtl', False),
                        "note": "Adapter selected but not yet applied to model" if adapter_valid else "Adapter file not found"
                    },
                    processing_time_ms=(time.time() - stage_start) * 1000
                ))
            else:
                pipeline_stages.append(PipelineStage(
                    stage_name="adapter_selection",
                    status="skipped",
                    metadata={
                        "target_lang": target_lang,
                        "note": f"No adapter found for {target_lang}, using base model"
                    },
                    processing_time_ms=(time.time() - stage_start) * 1000
                ))
        except Exception as e:
            logger.error(f"Adapter selection failed: {e}")
            pipeline_stages.append(PipelineStage(
                stage_name="adapter_selection",
                status="error",
                metadata={"error": str(e)},
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        
        # Stage 5: Vaani Preparation
        stage_start = time.time()
        try:
            prosody_hint = generate_prosody_hint(
                text=current_output,
                lang=target_lang,
                tone=request.tone
            )
            
            if prosody_hint:
                is_valid = validate_prosody_hint(prosody_hint)
                prosody_hint_str = prosody_hint.get("prosody_hint", "default")
                episode_data["prosody_hint"] = prosody_hint_str
                
                # Process Vaani feedback (placeholder - will be updated when user provides feedback)
                try:
                    vaani_reward = process_vaani_feedback(None, None, prosody_hint_str, db)
                    rewards.append(vaani_reward)
                except Exception as e:
                    logger.warning(f"RL reward processing for Vaani failed: {e}")
                
                pipeline_stages.append(PipelineStage(
                    stage_name="vaani_prep",
                    status="success" if is_valid else "warning",
                    metadata={
                        "prosody_hint": prosody_hint_str,
                        "pitch": prosody_hint.get("pitch"),
                        "speed": prosody_hint.get("speed"),
                        "emphasis": prosody_hint.get("emphasis"),
                        "validated": is_valid,
                        "tone": request.tone,
                        "target_lang": target_lang
                    },
                    processing_time_ms=(time.time() - stage_start) * 1000
                ))
            else:
                pipeline_stages.append(PipelineStage(
                    stage_name="vaani_prep",
                    status="error",
                    metadata={
                        "error": "Failed to generate prosody hint",
                        "tone": request.tone,
                        "target_lang": target_lang
                    },
                    processing_time_ms=(time.time() - stage_start) * 1000
                ))
        except Exception as e:
            logger.error(f"Vaani preparation failed: {e}")
            pipeline_stages.append(PipelineStage(
                stage_name="vaani_prep",
                status="error",
                metadata={"error": str(e)},
                processing_time_ms=(time.time() - stage_start) * 1000
            ))
        
        return SovereignInferResponse(
            output=current_output,
            target_lang=target_lang,
            pipeline_stages=pipeline_stages,
            metadata={
                "source_lang": request.lang,
                "tone": request.tone,
                "pipeline_version": "1.0.0-day5",
                "episode_id": episode_id,
                "rewards_count": len(rewards)
            }
        )
        
    except Exception as e:
        logger.error(f"Sovereign inference failed: {e}")
        raise HTTPException(
            status_code=500,
            detail=f"Sovereign inference pipeline failed: {str(e)}"
        )


@router.get("/health")
async def health_check():
    """Health check endpoint for Sovereign service"""
    from app.services.sovereign_lm_core import is_model_loaded
    
    return {
        "status": "ok",
        "model_loaded": is_model_loaded(),
        "service": "sovereign_fusion_layer"
    }

