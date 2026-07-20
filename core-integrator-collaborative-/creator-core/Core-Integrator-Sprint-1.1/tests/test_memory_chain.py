import tempfile
import os
from db.memory import ContextMemory

def test_memory_chain_limit():
    """Test that memory stores only 5 entries per user per module"""
    # Use temporary file database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    memory = None
    try:
        memory = ContextMemory(db_path)
        user_id = "test_user_123"
        module = "finance"
        
        # Store 6 interactions
        for i in range(6):
            request_data = {
                "module": module,
                "intent": "generate",
                "data": {"test": f"request_{i+1}"}
            }
            response_data = {
                "status": "success",
                "message": "Test response",
                "result": {"test": f"result_{i+1}"}
            }
            memory.store_interaction(user_id, request_data, response_data)
        
        # Get history and verify only 5 entries remain
        history = memory.get_user_history(user_id)
        
        assert len(history) == 5, f"Expected 5 entries, got {len(history)}"
        
        # Verify all entries are for correct module
        for entry in history:
            assert entry["module"] == module
        
        # Verify entries are in correct order (newest first)
        assert "request_6" in str(history[0]["request"])
        assert "request_2" in str(history[4]["request"])
    
    finally:
        # Close database connection before deleting file
        if memory:
            del memory
        try:
            os.unlink(db_path)
        except (OSError, PermissionError):
            # File might be locked on Windows, ignore
            pass

def test_cross_module_isolation():
    """Test that different modules maintain separate 5-entry limits"""
    # Use temporary file database for testing
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    memory = None
    try:
        memory = ContextMemory(db_path)
        user_id = "isolation_test"
        
        # Add 3 finance entries
        for i in range(3):
            request_data = {"module": "finance", "intent": "generate", "data": {"test": f"finance_{i+1}"}}
            response_data = {"status": "success", "message": "Finance response", "result": {}}
            memory.store_interaction(user_id, request_data, response_data)
        
        # Add 3 education entries
        for i in range(3):
            request_data = {"module": "education", "intent": "generate", "data": {"test": f"education_{i+1}"}}
            response_data = {"status": "success", "message": "Education response", "result": {}}
            memory.store_interaction(user_id, request_data, response_data)
        
        # Verify total entries (should be 6: 3 finance + 3 education)
        history = memory.get_user_history(user_id)
        assert len(history) == 6
        
        # Count entries per module
        finance_count = sum(1 for entry in history if entry["module"] == "finance")
        education_count = sum(1 for entry in history if entry["module"] == "education")
        
        assert finance_count == 3
        assert education_count == 3
    
    finally:
        # Close database connection before deleting file
        if memory:
            del memory
        try:
            os.unlink(db_path)
        except (OSError, PermissionError):
            # File might be locked on Windows, ignore
            pass