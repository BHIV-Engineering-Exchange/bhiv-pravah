"""
MITRA Load Testing Configuration
---------------------------------
Uses Locust for production load testing.
Run: locust -f deploy/loadtest/locustfile.py --host=http://localhost:8000
"""
from locust import HttpUser, task, between
import json
import random
import string


def random_string(length=10):
    return "".join(random.choices(string.ascii_lowercase, k=length))


class MitraUser(HttpUser):
    wait_time = between(1, 3)
    host = "http://localhost:8000"

    def on_start(self):
        """Setup: get API key from environment."""
        self.api_key = "mitra_production_api_key_2026_secure_random_value"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    @task(10)
    def health_check(self):
        self.client.get("/health")

    @task(5)
    def root_endpoint(self):
        self.client.get("/")

    @task(20)
    def chat_general(self):
        messages = [
            "Hello, what can you do?",
            "Tell me about BHIV ecosystem",
            "What is the weather today?",
            "Help me with a task",
            "Explain machine learning",
        ]
        payload = {
            "version": "3.0.0",
            "input": {"message": random.choice(messages)},
            "context": {"platform": "web", "device": "desktop"},
        }
        self.client.post(
            "/api/assistant",
            headers=self.headers,
            json=payload,
        )

    @task(15)
    def chat_task_creation(self):
        tasks = [
            "Send an email to john@example.com with subject 'Meeting'",
            "Remind me to call mom tomorrow at 5pm",
            "Create a calendar event called 'Team Standup'",
            "Send a WhatsApp message to +1234567890 saying hello",
        ]
        payload = {
            "version": "3.0.0",
            "input": {"message": random.choice(tasks)},
            "context": {"platform": "web", "device": "desktop"},
        }
        self.client.post(
            "/api/assistant",
            headers=self.headers,
            json=payload,
        )

    @task(5)
    def metrics(self):
        self.client.get("/api/metrics", headers=self.headers)

    @task(3)
    def ecosystem_products(self):
        self.client.get("/api/ecosystem/products", headers=self.headers)

    @task(2)
    def ecosystem_health(self):
        self.client.get("/api/ecosystem/health", headers=self.headers)

    @task(2)
    def replay_stages(self):
        self.client.get(
            "/api/replay/test_trace_id/stages",
            headers=self.headers,
        )


class MitraStressUser(HttpUser):
    """High-frequency stress test user."""
    wait_time = between(0.1, 0.5)
    host = "http://localhost:8000"

    def on_start(self):
        self.api_key = "mitra_production_api_key_2026_secure_random_value"
        self.headers = {
            "X-API-Key": self.api_key,
            "Content-Type": "application/json",
        }

    @task(50)
    def rapid_fire_chat(self):
        payload = {
            "version": "3.0.0",
            "input": {"message": f"Stress test message {random_string(5)}"},
            "context": {"platform": "web", "device": "desktop"},
        }
        self.client.post(
            "/api/assistant",
            headers=self.headers,
            json=payload,
        )
