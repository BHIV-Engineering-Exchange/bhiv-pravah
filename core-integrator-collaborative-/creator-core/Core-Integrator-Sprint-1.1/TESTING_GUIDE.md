# Testing Guide

## Memory Chain Test

If you need to test the 5-entry memory limit per user per module, create this test file:

### File: `tests/test_memory_chain.py`

```python
from fastapi.testclient import TestClient
from main import app

client = TestClient(app)

def test_memory_chain_limit():
    """Test that memory stores only 5 entries per user per module"""
    user_id = "test_user_123"
    module = "finance"
    
    # Send 6 sequential requests to the same user and module
    for i in range(6):
        response = client.post("/core", json={
            "module": module,
            "intent": "generate",
            "user_id": user_id,
            "data": {"test_data": f"request_{i+1}"}
        })
        assert response.status_code == 200
    
    # Get history for the user
    response = client.get(f"/get-history?user_id={user_id}")
    assert response.status_code == 200
    
    history = response.json()
    
    # Assert exactly 5 entries remain (memory limit enforced)
    assert len(history) == 5
    
    # Verify all entries are for the correct module
    for entry in history:
        assert entry["module"] == module
```

### Setup Steps:

1. **Create tests directory:**
   ```bash
   mkdir tests
   echo. > tests/__init__.py
   ```

2. **Add testing dependencies to requirements.txt:**
   ```
   pytest>=7.0.0
   httpx>=0.24.0
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Run test:**
   ```bash
   pytest tests/test_memory_chain.py -v
   ```

### ⚠️ Warning

This test will add data to your main database (`db/context.db`). The test creates 6 interactions for "test_user_123" but only 5 will remain due to the memory limit.

### Cleanup (Optional)

To remove test data after testing:
```python
# Add to test file
def cleanup_test_data():
    from db.memory import ContextMemory
    memory = ContextMemory()
    # Manual cleanup would require direct SQL access
```