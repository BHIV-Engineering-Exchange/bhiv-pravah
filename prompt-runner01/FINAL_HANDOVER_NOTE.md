# FINAL HANDOVER NOTE

## Universal Prompt Runner v2 — Spec-Compliant Release

### System Overview

The Universal Prompt Runner is a domain-agnostic routing engine that converts any user prompt (natural language or structured) into a deterministic JSON instruction for downstream modules.

### Output Format (SYSTEM ROLE Specification)

```json
{
  "module": "<target_module>",
  "intent": "<detected_intent>",
  "data": {
    "topic": "<main_topic>",
    "parameters": {},
    "original_prompt": "<user_input>"
  },
  "tasks": [],
  "output_format": "<expected_result_format>",
  "context": {
    "source": "prompt_runner"
  }
}
```

### Architecture

**Processing Pipeline (internal):**
1. `PluginLoader` — loads all domain plugins from `plugins/` directory
2. `DomainDetector` — classifies domain via keyword/pattern scoring
3. `IntentDetector` — classifies intent within the domain
4. `EntityExtractor` — extracts structured parameters from the prompt
5. `ConstraintExtractor` — extracts constraint metadata
6. `InstructionBuilder` — assembles final spec-compliant instruction

**Adding a new domain:** Drop a `plugin.json` in `plugins/<domain>/` — no core code changes needed.

### Domains Supported

| Domain       | Module                | Key Intents                                    |
|--------------|-----------------------|------------------------------------------------|
| architecture | architecture_design   | design_building, analyze_site, calculate_estimate |
| legal        | legal_compliance      | analyze_contract, legal_research, draft_document |
| finance      | investment_analyzer   | analyze_investment, assess_risk, budget_planning |
| healthcare   | patient_assessor      | patient_assessment, treatment_planning, medical_research |
| software     | system_designer       | system_design, code_review, database_design    |
| general      | creator               | generate_explanation, generate_summary, process_request |

### Validation

Run: `python validate_integration.py`

Expected: **146/146 tests passing**

### Integration

Entry point: `PlatformAdapter.process(input_data)` → `Dict[str, Any]`

- `input_data` can be a natural language string or structured dict
- Structured dict accepts: `domain`, `intent`, `topic`, `data`, `constraints`, `prompt`
- Returns: `{"status": "success", "instruction": {...}, "adapter_version": "2.0.0"}`
