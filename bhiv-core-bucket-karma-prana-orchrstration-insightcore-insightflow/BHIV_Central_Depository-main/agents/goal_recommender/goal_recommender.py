from typing import Dict
from utils.logger import logger

async def process(input_data: Dict) -> Dict:
    try:
        analysis = input_data.get("analysis", {})

        # If no analysis provided, use default sample data for testing
        if not analysis:
            logger.info("No analysis provided, using default sample data for testing")
            analysis = {
                "total": 1500,
                "positive": 2500,
                "negative": -1000
            }
        
        recommendations = []
        if analysis.get("total", 0) > 0:
            recommendations.append("Increase savings")
        else:
            recommendations.append("Reduce expenses")
        
        logger.debug(f"Goal recommender processed: {recommendations}")
        return {"recommendations": recommendations}
    except Exception as e:
        logger.error(f"Goal recommender error: {e}")
        return {"error": str(e)}