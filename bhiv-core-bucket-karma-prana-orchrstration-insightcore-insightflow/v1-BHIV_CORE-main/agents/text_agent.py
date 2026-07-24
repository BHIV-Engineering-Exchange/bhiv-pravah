import logging
import time
from typing import Dict, Any
import uuid
import requests
import json
from utils.logger import get_logger
from reinforcement.reward_functions import get_reward_from_output
from reinforcement.replay_buffer import replay_buffer
from config.settings import MODEL_CONFIG
import os

logger = get_logger(__name__)

class TextAgent:
    """Agent for processing text inputs using Ollama."""
    def __init__(self):
        self.model_config = MODEL_CONFIG.get("edumentor_agent", {})
        self.ollama_url = os.getenv("OLLAMA_URL", "http://localhost:11434/api/generate")
        self.model_name = "llama3.1"
        self.timeout = 30

    def process_text(self, text: str, task_id: str, retries: int = 3) -> Dict[str, Any]:
        """Summarize text using Ollama API with retry logic."""
        start_time = time.time()

        for attempt in range(retries):
            try:
                logger.info(f"Processing text (attempt {attempt + 1}/{retries}) for task {task_id}")

                prompt = f"Summarize the following text in 50-100 words: {text}"

                # Prepare Ollama request
                payload = {
                    "model": self.model_name,
                    "prompt": prompt,
                    "stream": False,
                    "options": {
                        "temperature": 0.7,
                        "top_p": 0.9,
                        "max_tokens": 200
                    }
                }

                headers = {
                    "Content-Type": "application/json",
                    "ngrok-skip-browser-warning": "true"
                }

                response = requests.post(
                    self.ollama_url,
                    json=payload,
                    headers=headers,
                    timeout=self.timeout
                )
                response.raise_for_status()

                result_data = response.json()
                summary = result_data.get("response", "No summary generated").strip()

                processing_time = time.time() - start_time

                logger.info(f"Text processing successful for task {task_id} in {processing_time:.2f}s")
                logger.debug(f"Input: {text[:100]}..., Summary: {summary[:100]}...")

                return {
                    "result": summary,
                    "model": "text_agent",
                    "tokens_used": len(text.split()) + len(summary.split()),  # Approximate
                    "cost_estimate": 0.0,  # Free tier for development
                    "status": 200,
                    "keywords": ["text", "summary"],
                    "processing_time": processing_time,
                    "inference_time": processing_time,  # For single API call
                    "attempts": attempt + 1
                }

            except Exception as e:
                processing_time = time.time() - start_time
                logger.warning(f"Text processing attempt {attempt + 1}/{retries} failed for task {task_id}: {str(e)}")

                if attempt < retries - 1:
                    # Wait before retry with exponential backoff
                    wait_time = 2 ** attempt
                    logger.info(f"Retrying in {wait_time} seconds...")
                    time.sleep(wait_time)
                else:
                    # Final attempt failed
                    logger.error(f"Text processing failed after {retries} attempts for task {task_id}: {str(e)}")
                    return {
                        "error": f"Text processing failed after {retries} attempts: {str(e)}",
                        "status": 500,
                        "keywords": [],
                        "processing_time": processing_time,
                        "attempts": retries
                    }

    def run(self, input_path: str, live_feed: str = "", model: str = "edumentor_agent", input_type: str = "text", task_id: str = None) -> Dict[str, Any]:
        task_id = task_id or str(uuid.uuid4())
        logger.info(f"TextAgent starting task {task_id} with input_type: {input_type}, model: {model}")

        # Enhanced logging with input metadata
        input_length = len(input_path) if input_path else 0
        logger.debug(f"Task {task_id} - Input length: {input_length} characters")

        result = self.process_text(input_path, task_id)

        # Add metadata to result
        result['agent'] = 'text_agent'
        result['input_type'] = input_type
        result['input_length'] = input_length

        reward = get_reward_from_output(result, task_id)
        replay_buffer.add_run(task_id, input_path, result, "text_agent", model, reward)

        logger.info(f"TextAgent completed task {task_id} with status: {result.get('status', 'unknown')}")
        return result

if __name__ == "__main__":
    agent = TextAgent()
    test_input = "Algebraic equations are mathematical statements that show the equality of two expressions. They often involve variables and constants and are used to model real-world problems. Solving these equations involves finding the values of the variables that make the equation true."
    result = agent.run(test_input, input_type="text")
    print(result)