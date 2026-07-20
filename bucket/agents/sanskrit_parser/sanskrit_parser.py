from typing import Dict
from utils.logger import logger

async def process(input_data: Dict) -> Dict:
    try:
        text = input_data.get("text", "")
        if not text:
            raise ValueError("No text provided")
        
        parsed = {
            "root": text.split()[0],
            "meaning": "parsed"
        }
        
        logger.debug(f"Sanskrit parser processed: {parsed}")
        return {"parsed": parsed}
    except Exception as e:
        logger.error(f"Sanskrit parser error: {e}")
        return {"error": str(e)}