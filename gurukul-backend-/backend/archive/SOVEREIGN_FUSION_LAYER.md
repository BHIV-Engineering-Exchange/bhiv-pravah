# Sovereign Polyglot Fusion Layer Documentation

## Overview

The Sovereign Polyglot Fusion Layer is a unified multilingual inference engine that integrates:
- **LM Core**: Fine-tuned Llama 3.2 3B model for language understanding
- **KSML Processor**: Knowledge Structure Markup Language for semantic annotation
- **Adapter Registry**: Language-specific adapters (currently Arabic)
- **Vaani RL-TTS**: Prosody mapping for text-to-speech
- **RL Loop**: Unified reinforcement learning system for continuous improvement

## Architecture

```
Input Text
    ↓
[LM Core] → Generates multilingual output
    ↓
[KSML Processor] → Adds semantic labels & educational context
    ↓
[RL Processing] → Collects rewards from all stages
    ↓
[Adapter Selection] → Selects language-specific adapter
    ↓
[Vaani Prep] → Generates prosody hints for TTS
    ↓
Output (with metadata)
```

## Components

### 1. LM Core (`sovereign_lm_core.py`)

**Purpose**: Loads and runs inference with the fine-tuned Llama 3.2 3B model.

**Key Functions**:
- `load_model()`: Loads model from checkpoint
- `generate()`: Generates text from prompt

**Model Details**:
- Base: `unsloth/llama-3.2-3b-instruct-bnb-4bit`
- Checkpoint: Loaded from `checkpoint_info.pkl`
- LoRA adapters: Merged for faster inference

### 2. KSML Processor (`ksml_processor.py`)

**Purpose**: Adds semantic labels and educational context to text.

**Key Functions**:
- `annotate_with_ksml()`: Annotates text with KSML labels

**Labels Generated**:
- Language detection
- Question/example/definition detection
- Topic extraction
- Structure analysis

### 3. Adapter Registry (`adapter_registry.py`)

**Purpose**: Manages language-specific adapters for fine-tuning.

**Current Support**:
- Arabic (`ar`): RTL support, 50K tokens, 2GB VRAM

**Key Functions**:
- `get_adapter_for_language()`: Auto-selects adapter by language
- `validate_adapter()`: Validates adapter file exists

### 4. Prosody Mapper (`prosody_mapper.py`)

**Purpose**: Maps language and tone to prosody hints for TTS.

**Supported Tones** (Arabic):
- `neutral`: Balanced speech
- `excited`: Enthusiastic, energetic
- `educational`: Clear, instructional
- `formal`: Professional, authoritative
- `friendly`: Warm, conversational
- `calm`: Relaxed, soothing

**Key Functions**:
- `generate_prosody_hint()`: Generates prosody configuration
- `validate_prosody_hint()`: Validates prosody configuration

### 5. RL Loop (`rl_loop.py`)

**Purpose**: Processes rewards from all pipeline stages.

**Reward Sources**:
- `lm_core`: Output quality metrics
- `ksml`: Annotation accuracy
- `vaani`: User feedback on TTS

**Key Functions**:
- `process_lm_output()`: Generates LM quality reward
- `process_ksml_labels()`: Generates KSML accuracy reward
- `process_vaani_feedback()`: Processes user feedback
- `merge_episodes()`: Merges all rewards into unified store

### 6. Reward Manager (`reward_manager.py`)

**Purpose**: Manages unified reward table and policy updates.

**Key Functions**:
- `add_reward()`: Adds reward to store
- `get_unified_rewards()`: Retrieves aggregated rewards
- `update_policy()`: Updates RL policy
- `get_policy_stats()`: Gets policy statistics

## API Endpoints

### POST `/api/v1/sovereign/infer`

Unified inference endpoint.

**Request**:
```json
{
  "text": "What is mathematics?",
  "lang": "en",
  "target_lang": "ar",
  "tone": "educational"
}
```

**Response**:
```json
{
  "output": "ما هي الرياضيات؟",
  "target_lang": "ar",
  "pipeline_stages": [
    {
      "stage_name": "lm_core",
      "status": "success",
      "output": "...",
      "processing_time_ms": 1234.5
    },
    ...
  ],
  "metadata": {
    "episode_id": "ep_abc123",
    "rewards_count": 3
  }
}
```

### GET `/api/v1/sovereign/health`

Health check endpoint.

**Response**:
```json
{
  "status": "ok",
  "model_loaded": true,
  "service": "sovereign_fusion_layer"
}
```

### POST `/api/v1/vaani/compose/prosody_map`

Prosody mapping endpoint.

**Request**:
```json
{
  "text": "Hello",
  "language": "ar",
  "tone": "educational"
}
```

**Response**:
```json
{
  "prosody_hint": "educational_ar",
  "pitch": 0.55,
  "speed": 0.95,
  "emphasis": 0.4,
  "pause_duration": 0.25
}
```

## Database Models

### RLEpisode
Stores inference episodes with pipeline outputs.

**Fields**:
- `episode_id`: Unique episode identifier
- `source_text`: Original input text
- `target_lang`: Target language
- `lm_output`: LM-generated output
- `ksml_labels`: KSML annotations
- `prosody_hint`: Prosody hint used

### RLReward
Stores individual rewards from different sources.

**Fields**:
- `episode_id`: Foreign key to RLEpisode
- `source`: Reward source (`lm_core`, `ksml`, `vaani`)
- `reward_value`: Reward score (0.0 to 1.0)
- `reward_type`: Type of reward
- `context`: Additional context

### RLPolicy
Stores RL policy state and parameters.

**Fields**:
- `policy_name`: Policy identifier
- `language`: Language code
- `parameters`: Policy parameters (JSON)
- `average_reward`: Average reward score
- `total_episodes`: Total episodes processed

## Configuration

### Checkpoint Info
Model checkpoint information is loaded from `checkpoint_info.pkl`:
- `checkpoint_path`: Path to model checkpoint
- `base_model_name`: Base model identifier
- `model_type`: Model type (CAUSAL_LM)

### Adapter Registry
Adapter configurations in `backend/adapters/registry.json`:
- Language metadata
- VRAM requirements
- Token counts
- Version information

### Prosody Mappings
Prosody configurations in `backend/data/prosody_mappings.json`:
- Language-specific tone mappings
- Pitch, speed, emphasis parameters
- Prosody hint identifiers

## Language Support

### Current: Arabic (ar)
- RTL support
- 6 tone variations
- Full pipeline support

### Future Expansion
The system is designed to support additional languages by:
1. Adding adapter to `registry.json`
2. Adding prosody mappings
3. Adding evaluation cards

## Evaluation

Evaluation engine uses:
- **BLEU**: N-gram precision
- **ROUGE**: Recall-oriented metrics
- **COMET-lite**: Semantic similarity

Test cases in `backend/eval_cards/ar.json` for Arabic evaluation.

## Dependencies

Key dependencies:
- `torch`: PyTorch for model inference
- `transformers`: Hugging Face transformers
- `peft`: Parameter-efficient fine-tuning
- `sqlalchemy`: Database ORM
- `fastapi`: API framework

See `requirements.txt` for full list.

## Performance

**Model Loading**:
- First load: ~30-60 seconds (depends on hardware)
- Subsequent calls: Instant (cached)

**Inference Speed**:
- LM generation: ~1-3 seconds per request
- KSML processing: <100ms
- Full pipeline: ~2-5 seconds

**Memory Requirements**:
- Model: ~2-4GB VRAM
- Adapters: ~2GB VRAM per adapter
- Total: ~4-6GB VRAM recommended

## Troubleshooting

### Model Not Loading
- Check `checkpoint_info.pkl` exists
- Verify checkpoint path is correct
- Ensure sufficient VRAM available

### Adapter Not Found
- Check `adapters/registry.json` exists
- Verify adapter file path
- Ensure adapter file exists on disk

### RL Rewards Not Saving
- Check database connection
- Verify `rl_episodes` and `rl_rewards` tables exist
- Check database session is passed correctly

## Future Enhancements

1. **Multi-language Support**: Expand beyond Arabic
2. **Advanced RL**: Implement policy gradient methods
3. **Quality Models**: Add actual quality scoring models
4. **Caching**: Add response caching for common queries
5. **Monitoring**: Add metrics and monitoring dashboard

