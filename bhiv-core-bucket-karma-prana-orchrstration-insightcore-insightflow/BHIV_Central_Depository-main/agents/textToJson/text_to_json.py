"""
Text-to-JSON Agent
Calls the deployed Prompt-to-JSON API endpoints
"""

import os
import asyncio
import aiohttp
from typing import Dict, Any, List
from utils.logger import logger

# API Configuration
BASE_URL = "https://prompt-to-json-backend.onrender.com"
API_KEY = os.getenv("PROMPT_TO_JSON_API_KEY", "test-api-key")  # Set this in environment
JWT_TOKEN = None  # Will be obtained via /token endpoint

class APIClient:
    def __init__(self, jwt_token=None):
        self.base_url = BASE_URL
        self.api_key = API_KEY
        self.jwt_token = jwt_token
        self.session = None

    async def __aenter__(self):
        self.session = aiohttp.ClientSession()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.close()

    async def _get_headers(self, include_jwt: bool = True, include_api_key: bool = True):
        """Get headers for API requests"""
        headers = {
            "Content-Type": "application/json"
        }
        if include_api_key:
            headers["X-API-Key"] = self.api_key
        if include_jwt and self.jwt_token:
            headers["Authorization"] = f"Bearer {self.jwt_token}"
        return headers

    async def authenticate(self):
        """Get JWT token for authenticated requests"""
        try:
            # Use demo credentials if available
            username = os.getenv("DEMO_USERNAME", "demo")
            password = os.getenv("DEMO_PASSWORD", "demo")

            auth_data = {
                "username": username,
                "password": password
            }

            headers = await self._get_headers(include_jwt=False, include_api_key=False)
            async with self.session.post(f"{self.base_url}/token", json=auth_data, headers=headers) as response:
                if response.status == 200:
                    data = await response.json()
                    self.jwt_token = data.get("access_token")
                    logger.info("Successfully authenticated with API")
                    return True
                else:
                    logger.warning(f"Authentication failed: {response.status}")
                    return False
    except Exception as e:
        logger.error(f"Authentication error: {e}")
        return False

    async def call_endpoint(self, endpoint: str, method: str = "GET", data: Dict = None) -> Dict:
        """Call a specific API endpoint"""
        try:
            url = f"{self.base_url}{endpoint}"
            headers = await self._get_headers()

            logger.info(f"Calling {method} {url}")

            if method == "GET":
                async with self.session.get(url, headers=headers) as response:
                    return await self._handle_response(response, endpoint)
            elif method == "POST":
                async with self.session.post(url, json=data, headers=headers) as response:
                    return await self._handle_response(response, endpoint)
            else:
                return {"error": f"Unsupported method: {method}"}

        except Exception as e:
            logger.error(f"Error calling {endpoint}: {e}")
            return {"error": str(e)}

    async def _handle_response(self, response, endpoint: str) -> Dict:
        """Handle API response"""
        try:
            if response.status == 200:
                data = await response.json()
                logger.info(f"Successfully called {endpoint}")
                return {"success": True, "data": data}
            else:
                error_text = await response.text()
                logger.error(f"API call to {endpoint} failed: {response.status} - {error_text}")
                return {"success": False, "error": f"HTTP {response.status}: {error_text}"}
        except Exception as e:
            logger.error(f"Error handling response from {endpoint}: {e}")
            return {"success": False, "error": str(e)}

async def call_generate(client: APIClient, prompt: str) -> Dict:
    """Call /generate endpoint"""
    data = {"prompt": prompt}
    return await client.call_endpoint("/generate", "POST", data)

async def call_evaluate(client: APIClient, spec: Dict, prompt: str) -> Dict:
    """Call /evaluate endpoint"""
    data = {"spec": spec, "prompt": prompt}
    return await client.call_endpoint("/evaluate", "POST", data)

async def call_iterate(client: APIClient, prompt: str, n_iter: int = 3) -> Dict:
    """Call /iterate endpoint"""
    data = {"prompt": prompt, "n_iter": n_iter}
    return await client.call_endpoint("/iterate", "POST", data)

async def call_health(client: APIClient) -> Dict:
    """Call /health endpoint"""
    return await client.call_endpoint("/health", "GET")

async def call_metrics(client: APIClient) -> Dict:
    """Call /basic-metrics endpoint"""
    return await client.call_endpoint("/basic-metrics", "GET")

async def call_all_endpoints(client: APIClient, input_data: Dict) -> Dict:
    """Call all relevant endpoints based on input"""
    results = {}
    errors = []

    # Always call health
    health_result = await call_health(client)
    results["health"] = health_result

    action = input_data.get("action", "all")

    if action in ["generate", "all"]:
        prompt = input_data.get("prompt", "Create a modern web application specification")
        generate_result = await call_generate(client, prompt)
        results["generate"] = generate_result
        if not generate_result.get("success"):
            errors.append(f"Generate failed: {generate_result.get('error')}")

    if action in ["evaluate", "all"] and "spec" in input_data:
        spec = input_data.get("spec", {})
        prompt = input_data.get("prompt", "Evaluate this specification")
        evaluate_result = await call_evaluate(client, spec, prompt)
        results["evaluate"] = evaluate_result
        if not evaluate_result.get("success"):
            errors.append(f"Evaluate failed: {evaluate_result.get('error')}")

    if action in ["iterate", "all"]:
        prompt = input_data.get("prompt", "Create an optimal specification through reinforcement learning")
        n_iter = input_data.get("n_iter", 3)
        iterate_result = await call_iterate(client, prompt, n_iter)
        results["iterate"] = iterate_result
        if not iterate_result.get("success"):
            errors.append(f"Iterate failed: {iterate_result.get('error')}")

    if action in ["metrics", "all"]:
        metrics_result = await call_metrics(client)
        results["metrics"] = metrics_result
        if not metrics_result.get("success"):
            errors.append(f"Metrics failed: {metrics_result.get('error')}")

    return {
        "result": results,
        "success": len(errors) == 0,
        "errors": errors
    }

async def process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Main agent processing function.
    Calls the Prompt-to-JSON API endpoints based on the action specified.
    """
    try:
        logger.info(f"Processing textToJson request: {input_data.get('action', 'all')}")

        jwt_token = input_data.get("jwt_token")
        async with APIClient(jwt_token=jwt_token) as client:
            # Try to authenticate if no JWT token provided
            if not jwt_token:
                await client.authenticate()

            # Call appropriate endpoints
            result = await call_all_endpoints(client, input_data)

            logger.info(f"textToJson processing completed with success: {result['success']}")
            return result

    except Exception as e:
        logger.error(f"textToJson processing failed: {e}")
        return {
            "result": {},
            "success": False,
            "errors": [str(e)]
        }
