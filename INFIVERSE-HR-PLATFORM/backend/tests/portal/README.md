# Portal UI Tests

This directory contains all portal user interface test files for the BHIV HR Platform.

## Files

- `candidate_portal_ui_simple.py` - Simple candidate portal UI tests
- `candidate_portal_ui_test.py` - Comprehensive candidate portal UI tests
- `client_portal_ui_test.py` - Client portal UI integration tests
- `complete_candidate_pipeline_test.py` - End-to-end candidate pipeline tests
- `complete_client_pipeline_test.py` - End-to-end client pipeline tests
- `comprehensive_client_portal_test.py` - Comprehensive client portal testing

## Portal Services

- **HR Portal**: bhiv-hr-portal-u670.onrender.com/
- **Client Portal**: bhiv-hr-client-portal-3iod.onrender.com/
- **Candidate Portal**: bhiv-hr-candidate-portal-abe6.onrender.com/

## Usage

```bash
# Run all portal UI tests
python -m pytest tests/portal/

# Run specific portal test
python tests/portal/candidate_portal_ui_test.py
```

## Test Requirements

- Streamlit 1.41.1
- Selenium WebDriver (for UI automation)
- Production portal URLs configured