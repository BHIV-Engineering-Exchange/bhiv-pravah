# Sovereign Fusion Layer Tests

## Overview

This directory contains smoke tests for the Sovereign Fusion Layer. These tests verify basic functionality without requiring full model loading or database setup.

## Running Tests

### Run All Tests

```bash
cd backend
pytest tests/test_sovereign_smoke.py -v
```

### Run Specific Test Class

```bash
pytest tests/test_sovereign_smoke.py::TestKSMLProcessor -v
```

### Run Specific Test

```bash
pytest tests/test_sovereign_smoke.py::TestKSMLProcessor::test_annotate_basic -v
```

## Test Coverage

### Unit Tests

1. **KSML Processor** (`TestKSMLProcessor`)
   - Basic annotation
   - Arabic text annotation

2. **Adapter Registry** (`TestAdapterRegistry`)
   - Registry loading
   - Arabic adapter retrieval
   - Adapter validation

3. **Prosody Mapper** (`TestProsodyMapper`)
   - Prosody hint generation
   - Prosody validation
   - Available tones

4. **Metrics** (`TestMetrics`)
   - BLEU score calculation
   - ROUGE score calculation
   - COMET-lite score calculation

5. **Evaluation Engine** (`TestEvaluationEngine`)
   - Evaluation card loading
   - Card structure validation

6. **Integration** (`TestIntegration`)
   - Component imports
   - Schema validation

## Prerequisites

- Python 3.9+
- pytest installed: `pip install pytest`
- All dependencies from `requirements.txt`

## Expected Results

All tests should pass. If any test fails:

1. Check that all required files exist:
   - `adapters/registry.json`
   - `data/prosody_mappings.json`
   - `eval_cards/ar.json`

2. Verify imports work:
   ```bash
   python -c "from app.services.ksml_processor import annotate_with_ksml; print('OK')"
   ```

3. Check file paths are correct

## Adding New Tests

When adding new functionality:

1. Add test class following naming convention: `Test<ComponentName>`
2. Add test methods: `test_<functionality>`
3. Use descriptive assertions
4. Test both success and failure cases

## Continuous Integration

These tests can be integrated into CI/CD pipelines:

```yaml
# Example GitHub Actions
- name: Run Smoke Tests
  run: |
    cd backend
    pytest tests/test_sovereign_smoke.py -v
```

