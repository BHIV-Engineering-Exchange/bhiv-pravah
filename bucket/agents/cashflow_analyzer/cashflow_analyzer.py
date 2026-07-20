from typing import Dict
from utils.logger import logger

async def process(input_data: Dict) -> Dict:
    try:
        transactions = input_data.get("transactions", [])

        # If no transactions provided, use default sample data for testing
        if not transactions:
            logger.info("No transactions provided, using default sample data for testing")
            transactions = [
                {"id": 1, "amount": 2000, "description": "Sample Salary"},
                {"id": 2, "amount": -800, "description": "Sample Rent"},
                {"id": 3, "amount": -200, "description": "Sample Groceries"},
                {"id": 4, "amount": 500, "description": "Sample Freelance Income"}
            ]
        
        total = sum(t["amount"] for t in transactions)
        positive = sum(t["amount"] for t in transactions if t["amount"] > 0)
        negative = sum(t["amount"] for t in transactions if t["amount"] < 0)
        
        analysis = {
            "total": total,
            "positive": positive,
            "negative": negative
        }
        
        logger.debug(f"Cashflow analysis: {analysis}")
        return {"analysis": analysis}
    except Exception as e:
        logger.error(f"Cashflow analyzer error: {e}")
        return {"error": str(e)}