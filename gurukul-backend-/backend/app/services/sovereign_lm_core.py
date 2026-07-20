"""
Sovereign LM Core - Fine-tuned Language Model Service

This service loads and manages the fine-tuned Llama 3.2 3B model with LoRA adapters
for use as the Language Model Core in the Sovereign Polyglot Fusion Layer.

Model Details:
- Base: unsloth/llama-3.2-3b-instruct-bnb-4bit
- Fine-tuned with LoRA adapters
- Checkpoint: Loaded from checkpoint_info.pkl
"""

import os
import pickle
from pathlib import Path
from typing import Optional, Dict, Any
import logging

logger = logging.getLogger(__name__)

# Optional ML imports - may not be installed in lightweight deployment
try:
    import torch
    from transformers import AutoTokenizer, AutoModelForCausalLM
    from peft import PeftModel
    ML_AVAILABLE = True
except ImportError:
    ML_AVAILABLE = False
    logger.warning("torch/transformers/peft not installed. Sovereign LM features disabled.")

# Global model instance (lazy loaded)
_model_instance: Optional[Any] = None
_tokenizer_instance: Optional[Any] = None


def _load_checkpoint_info() -> Dict[str, Any]:
    """
    Load checkpoint information from checkpoint_info.pkl
    
    Returns:
        dict: Checkpoint information containing model path and config
    """
    checkpoint_info_path = Path(__file__).parent.parent.parent.parent / "checkpoint_info.pkl"
    
    if not checkpoint_info_path.exists():
        raise FileNotFoundError(
            f"checkpoint_info.pkl not found at {checkpoint_info_path}. "
            "Please ensure the checkpoint info file exists in the project root."
        )
    
    with open(checkpoint_info_path, 'rb') as f:
        checkpoint_info = pickle.load(f)
    
    return checkpoint_info


def _load_model_from_checkpoint(checkpoint_path: str, base_model_name: str) -> tuple:
    """
    Load fine-tuned model and tokenizer from checkpoint
    
    Args:
        checkpoint_path: Path to the model checkpoint directory
        base_model_name: Name of the base model to load
        
    Returns:
        tuple: (model, tokenizer)
    """
    checkpoint_path_obj = Path(checkpoint_path)
    
    if not checkpoint_path_obj.exists():
        raise FileNotFoundError(
            f"Checkpoint not found at {checkpoint_path}. "
            "Please verify the checkpoint path in checkpoint_info.pkl"
        )
    
    logger.info(f"Loading base model: {base_model_name}")
    
    # Load tokenizer
    tokenizer = AutoTokenizer.from_pretrained(checkpoint_path)
    
    # Try to load from checkpoint directly first (if it's a full model)
    try:
        logger.info(f"Attempting to load model directly from checkpoint: {checkpoint_path}")
        model = AutoModelForCausalLM.from_pretrained(
            checkpoint_path,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map="auto" if torch.cuda.is_available() else "cpu",
            trust_remote_code=True
        )
        logger.info("✓ Model loaded directly from checkpoint")
    except Exception as e:
        logger.info(f"Direct checkpoint load failed, trying base model + adapters: {e}")
        # Fallback: Load base model and then adapters
        device_map = "auto" if torch.cuda.is_available() else "cpu"
        base_model = AutoModelForCausalLM.from_pretrained(
            base_model_name,
            torch_dtype=torch.float16 if torch.cuda.is_available() else torch.float32,
            device_map=device_map,
            trust_remote_code=True
        )
        
        # Load LoRA adapters if they exist
        adapter_path = checkpoint_path_obj / "adapter_model"
        if adapter_path.exists():
            logger.info(f"Loading LoRA adapters from {adapter_path}")
            model = PeftModel.from_pretrained(base_model, str(adapter_path))
            model = model.merge_and_unload()  # Merge adapters for faster inference
        else:
            logger.warning("No LoRA adapters found, using base model only")
            model = base_model
    
    model.eval()  # Set to evaluation mode
    
    logger.info("✓ Model loaded successfully")
    return model, tokenizer


def get_model() -> tuple:
    """
    Get or load the fine-tuned model instance (lazy loading)
    
    Returns:
        tuple: (model, tokenizer) - The loaded model and tokenizer
        
    Raises:
        FileNotFoundError: If checkpoint files are not found
        RuntimeError: If model loading fails
    """
    global _model_instance, _tokenizer_instance
    
    if _model_instance is not None and _tokenizer_instance is not None:
        return _model_instance, _tokenizer_instance
    
    try:
        # Load checkpoint info
        checkpoint_info = _load_checkpoint_info()
        checkpoint_path = checkpoint_info.get('checkpoint_path')
        base_model_name = checkpoint_info.get('base_model_name')
        
        if not checkpoint_path or not base_model_name:
            raise ValueError(
                "checkpoint_info.pkl missing required fields: 'checkpoint_path' or 'base_model_name'"
            )
        
        # Load model and tokenizer
        _model_instance, _tokenizer_instance = _load_model_from_checkpoint(
            checkpoint_path, base_model_name
        )
        
        return _model_instance, _tokenizer_instance
        
    except Exception as e:
        logger.error(f"Failed to load model: {e}")
        raise RuntimeError(f"Model loading failed: {str(e)}") from e


async def generate(
    prompt: str,
    system_prompt: Optional[str] = None,
    max_tokens: int = 512,
    temperature: float = 0.7,
    top_p: float = 0.9
) -> str:
    """
    Generate text using the fine-tuned model
    
    Args:
        prompt: User input text
        system_prompt: Optional system instruction
        max_tokens: Maximum tokens to generate
        temperature: Sampling temperature (0.0-1.0)
        top_p: Nucleus sampling parameter
        
    Returns:
        str: Generated text response
    """
    try:
        model, tokenizer = get_model()
        
        # Format prompt with system instruction if provided
        if system_prompt:
            formatted_prompt = f"System: {system_prompt}\n\nUser: {prompt}\n\nAssistant:"
        else:
            formatted_prompt = f"User: {prompt}\n\nAssistant:"
        
        # Tokenize input
        inputs = tokenizer(
            formatted_prompt,
            return_tensors="pt",
            truncation=True,
            max_length=2048
        )
        
        # Move inputs to same device as model
        device = next(model.parameters()).device
        inputs = {k: v.to(device) for k, v in inputs.items()}
        
        # Generate
        with torch.no_grad():
            outputs = model.generate(
                **inputs,
                max_new_tokens=max_tokens,
                temperature=temperature,
                top_p=top_p,
                do_sample=True,
                pad_token_id=tokenizer.eos_token_id
            )
        
        # Decode response
        generated_text = tokenizer.decode(outputs[0], skip_special_tokens=True)
        
        # Extract only the assistant's response (remove input prompt)
        if "Assistant:" in generated_text:
            response = generated_text.split("Assistant:")[-1].strip()
        else:
            response = generated_text[len(formatted_prompt):].strip()
        
        return response
        
    except Exception as e:
        logger.error(f"Generation failed: {e}")
        raise RuntimeError(f"Text generation failed: {str(e)}") from e


def is_model_loaded() -> bool:
    """
    Check if model is currently loaded
    
    Returns:
        bool: True if model is loaded, False otherwise
    """
    return _model_instance is not None and _tokenizer_instance is not None

