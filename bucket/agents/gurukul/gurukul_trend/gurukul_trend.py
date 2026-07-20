import os
import httpx
from typing import Dict
from utils.logger import logger

async def process(input_data: Dict) -> Dict:
    try:
        api_url = os.getenv("GURUKUL_TREND_API")
        if not api_url:
            logger.warning("GURUKUL_TREND_API not set, using mock data")
            return {
                "success": True,
                "trends": ["Mock trend 1", "Mock trend 2"],
                "note": "Using mock data - set GURUKUL_TREND_API in .env for real API"
            }
        
        logger.debug(f"Calling gurukul_trend API: {api_url} with input: {input_data}")
        async with httpx.AsyncClient() as client:
            response = await client.post(api_url, json=input_data, timeout=30)
            response.raise_for_status()
            result = response.json()
            logger.debug(f"Received response: {result}")
            return result
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error calling gurukul_trend API: {e.response.status_code} - {e.response.text}")
        return {"error": f"HTTP {e.response.status_code}: {e.response.text}"}
    except Exception as e:
        logger.error(f"Error calling gurukul_trend API: {str(e)}")
        return {"error": str(e)}