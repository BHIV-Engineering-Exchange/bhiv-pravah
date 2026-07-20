from typing import Dict, Any

class SampleTextModule:
    """Sample text processing module"""
    
    def process(self, data: Dict[str, Any], context: list = None) -> Dict[str, Any]:
        """Process input text and return word count"""
        input_text = data.get("input_text", "")
        word_count = len(input_text.split()) if input_text else 0
        
        return {
            "status": "success",
            "message": "Text processed successfully",
            "result": {"word_count": word_count}
        }