import os
import json
import asyncio
import aiohttp
from dotenv import load_dotenv
from utils.logger import logger

# Load environment variables
load_dotenv()

async def process(input_data):
    """
    Process the input data using the Financial Coordinator API and return the result.
    
    Args:
        input_data (dict): The input data containing the action and optional parameters
        
    Returns:
        dict: The processed result from the Financial Coordinator API
    """
    try:
        # Get API URL from environment variables
        api_url = os.getenv("FINANCIAL_COORDINATOR_API_URL")
        if not api_url:
            logger.warning("FINANCIAL_COORDINATOR_API_URL not set, using mock data")
            return {
                "success": True,
                "transactions": [
                    {"id": 1, "amount": 1000, "description": "Mock transaction", "type": "income"},
                    {"id": 2, "amount": -500, "description": "Mock expense", "type": "expense"}
                ],
                "note": "Using mock data - set FINANCIAL_COORDINATOR_API_URL in .env for real API"
            }
        
        # Extract action from input data
        action = input_data.get("action", "")
        if not action:
            logger.info("No action provided, using default 'get_transactions' for testing")
            action = "get_transactions"
        
        async with aiohttp.ClientSession() as session:
            if action == "get_transactions":
                # Get all transactions
                async with session.get(f"{api_url}/transactions") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "transactions": data.get("transactions", [])
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to fetch transactions: HTTP {response.status}"
                        }
                        
            elif action == "add_transaction":
                # Add a new transaction
                transaction = input_data.get("transaction", {})
                if not transaction:
                    return {"error": "No transaction data provided"}
                
                # Validate transaction data
                required_fields = ["amount", "description", "type"]
                for field in required_fields:
                    if field not in transaction:
                        return {"error": f"Missing required field '{field}' in transaction data"}
                
                async with session.post(
                    f"{api_url}/transactions", 
                    json={
                        "amount": transaction["amount"],
                        "description": transaction["description"],
                        "type": transaction["type"]
                    }
                ) as response:
                    if response.status == 200 or response.status == 201:
                        data = await response.json()
                        return {
                            "success": True,
                            "transaction": data
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to add transaction: HTTP {response.status}"
                        }
                        
            elif action == "get_report":
                # Get AI-generated financial report
                async with session.get(f"{api_url}/reports") as response:
                    if response.status == 200:
                        data = await response.json()
                        return {
                            "success": True,
                            "report": data.get("report", "No report available.")
                        }
                    else:
                        return {
                            "success": False,
                            "error": f"Failed to fetch report: HTTP {response.status}"
                        }
            else:
                return {"error": f"Unknown action: {action}. Use 'get_transactions', 'add_transaction', or 'get_report'"}
                
    except Exception as e:
        logger.error(f"Financial Coordinator API error: {str(e)}")
        return {"error": f"Financial Coordinator processing failed: {str(e)}"}

# For testing the agent directly
if __name__ == "__main__":
    # Test getting transactions
    test_input = {"action": "get_transactions"}
    result = asyncio.run(process(test_input))
    print("GET TRANSACTIONS RESULT:")
    print(json.dumps(result, indent=2))
    
    # Test getting report
    test_input = {"action": "get_report"}
    result = asyncio.run(process(test_input))
    print("\nGET REPORT RESULT:")
    print(json.dumps(result, indent=2))
    
    # Uncomment to test adding a transaction
    # test_input = {
    #     "action": "add_transaction",
    #     "transaction": {
    #         "amount": 100.50,
    #         "description": "Test transaction",
    #         "type": "income"
    #     }
    # }
    # result = asyncio.run(process(test_input))
    # print("\nADD TRANSACTION RESULT:")
    # print(json.dumps(result, indent=2))