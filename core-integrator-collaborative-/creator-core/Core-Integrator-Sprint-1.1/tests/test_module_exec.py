from modules.sample_text.module import SampleTextModule

def test_module_returns_proper_core_response():
    """Test that module returns proper CoreResponse format"""
    module = SampleTextModule()
    
    # Test with sample text
    data = {"input_text": "Hello world test"}
    response = module.process(data)
    
    # Verify CoreResponse structure
    assert "status" in response
    assert "message" in response
    assert "result" in response
    
    # Verify correct values
    assert response["status"] == "success"
    assert response["message"] == "Text processed successfully"
    assert response["result"]["word_count"] == 3

def test_module_empty_text():
    """Test module with empty text"""
    module = SampleTextModule()
    
    data = {"input_text": ""}
    response = module.process(data)
    
    assert response["status"] == "success"
    assert response["result"]["word_count"] == 0

def test_module_missing_input():
    """Test module with missing input_text"""
    module = SampleTextModule()
    
    data = {}
    response = module.process(data)
    
    assert response["status"] == "success"
    assert response["result"]["word_count"] == 0