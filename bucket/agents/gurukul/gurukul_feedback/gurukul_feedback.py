import os
import httpx
from typing import Dict
from utils.logger import logger

async def process(input_data: Dict) -> Dict:
    try:
        api_url = os.getenv("GURUKUL_FEEDBACK_API")
        if not api_url:
            logger.warning("GURUKUL_FEEDBACK_API not set, using mock data")
            return {
                "success": True,
                "feedback": "Mock feedback generated",
                "note": "Using mock data - set GURUKUL_FEEDBACK_API in .env for real API"
            }
        
        logger.debug(f"Calling gurukul_feedback API: {api_url} with input: {input_data}")
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=input_data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Received response: {result}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling gurukul_feedback API: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        logger.error(f"Error calling gurukul_feedback API: {str(e)}")
        return {"error": str(e)}