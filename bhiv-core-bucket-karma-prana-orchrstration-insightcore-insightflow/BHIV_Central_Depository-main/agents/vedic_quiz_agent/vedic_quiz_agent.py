from typing import Dict
from utils.logger import logger

async def process(input_data: Dict) -> Dict:
    try:
        question = input_data.get("question", "")
        if not question:
            raise ValueError("No question provided")
        
        # Mock response for testing
        answer = "Delhi" if "capital of India" in question.lower() else "Unknown"
        
        logger.debug(f"Vedic quiz agent processed: {question} -> {answer}")
        return {"answer": answer}
    except Exception as e:
        logger.error(f"Vedic quiz agent error: {e}")
        return {"error": str(e)}