"""
Prompt Runner - LLM Adapter (Groq API)
========================================
Connects to the Groq cloud API for deterministic prompt interpretation.

Responsibilities:
  - Infer domain and intent from the prompt
  - Generate context-specific tasks dynamically
  - Extract topic and output_format
  - Validate and sanitize the JSON instruction before returning

Requires:
  GROQ_API_KEY environment variable (or pass api_key= directly).

Usage:
    from llm_adapter import LLMAdapter
    adapter = LLMAdapter()
    instruction = adapter.generate_instruction("Explain how neural networks work")
"""

import json
import os
import re
import requests
from typing import Any, Dict, List, Optional


# ---------------------------------------------------------------------------
# Load local .env file (not committed) if present
# ---------------------------------------------------------------------------
def _load_local_env(path: str = ".env.local") -> None:
    """Load simple KEY=VALUE lines from a local env file into os.environ.
    This file is created locally and added to .gitignore to avoid committing
    secrets into the repository.
    """
    try:
        base = os.path.dirname(__file__)
        env_path = os.path.join(base, path)
        if not os.path.exists(env_path):
            return
        with open(env_path, "r", encoding="utf-8") as fh:  
            for raw in fh:
                line = raw.strip()
                if not line or line.startswith("#"):
                    continue
                if "=" not in line:
                    continue
                k, v = line.split("=", 1)
                k = k.strip()
                v = v.strip().strip('"').strip("'")
                if k and not os.environ.get(k):
                    os.environ[k] = v
    except Exception:
        # best-effort loader: never raise during import
        pass


# Load .env.local early so `GROQ_API_KEY` becomes available via os.environ
_load_local_env()

# ---------------------------------------------------------------------------
# Configuration
# ---------------------------------------------------------------------------

GROQ_API_URL    = "https://api.groq.com/openai/v1/chat/completions"
# Prefer a model that reliably follows strict JSON-only system prompts.
# llama-3.3-70b-versatile has the best instruction-following on Groq.
DEFAULT_MODEL   = "llama-3.3-70b-versatile"
REQUEST_TIMEOUT  = 30    # seconds — Groq is network-fast
MAX_PROMPT_CHARS = 6000  # truncate user prompts longer than this to stay under Groq payload limit

ALLOWED_MODULES = [
    "creator",
    "education",
    "finance",
    "workflow",
    "architecture",
    "legal",
    "analytics",
    "data_processing",
]

ALLOWED_OUTPUT_FORMATS = [
    "step_by_step_guide",
    "design_document",
    "analysis_report",
    "financial_estimate",
    "workflow_plan",
    "code_solution",
    "summary",
    "tutorial",
]

# ---------------------------------------------------------------------------
# System prompt sent to Groq for every /generate call
# ---------------------------------------------------------------------------

_SYSTEM_PROMPT = """\
You are Prompt Runner.

Your responsibility is to translate a user prompt into a deterministic, machine-readable JSON instruction that can be executed by downstream platform systems.

You must only interpret and structure the prompt.
You must not execute tasks, call tools, or generate content outputs.

OBJECTIVE:
Convert the user prompt into a structured instruction containing:
  module, intent, topic, tasks, output_format, product_context

The JSON must remain simple, deterministic, and consistent so that the Core Integrator can route the instruction correctly.

OUTPUT SCHEMA — always use this exact structure:
{
  "module": "",
  "intent": "",
  "topic": "",
  "tasks": [],
  "output_format": "",
  "product_context": "creator_core"
}

FIELD DEFINITIONS:
  module         — The system module responsible for handling the request.
  intent         — The primary objective of the request.
  topic          — A short description of the main subject of the request.
  tasks          — A list of short execution steps required to fulfill the request. Each task must be concise and machine-readable.
  output_format  — The expected structure of the final output.
  product_context — Indicates which product pipeline the request belongs to. Always set to: "creator_core" 

ARRAY RULE (IMPORTANT):
The tasks field must be a valid JSON array. Do NOT include numeric indexes.

Incorrect format:
"tasks": [0: "site_analysis", 1: "floor_plan_design"]

Correct format:
"tasks": ["site_analysis", "floor_plan_design", "structural_design"]

TASK RULES:
Tasks must be short, machine-readable execution steps.
Do not write long descriptive sentences.
Example:
"tasks": ["system_architecture_design", "data_pipeline_planning", "model_training_setup", "model_evaluation", "deployment_planning"]

JSON SYNTAX RULES:
- Add commas between fields.
- Arrays must contain only string values with no indexes.
- Return only valid JSON.
- No explanations. No markdown.

MODULE RULE — pick the best match from this list ONLY:
  creator, education, finance, workflow, architecture, legal, analytics, data_processing

DETERMINISTIC RULE:
The same prompt must always produce the same structure. Avoid randomness.

IMPORTANT RULES:
1. Output must always be valid JSON.
2. The following fields must always be present: module, intent, topic, tasks, output_format, product_context.
3. Do not omit the product_context field — its value must always be "creator_core".
4. Do not add extra fields.
5. Tasks must be short structured steps, not long sentences.

FINAL OUTPUT:
Return only valid JSON that follows the schema exactly.
"""


# ---------------------------------------------------------------------------
# Groq HTTP client
# ---------------------------------------------------------------------------

class GroqClient:
    """
    Thin wrapper around the Groq OpenAI-compatible Chat Completions API.
    Uses temperature=0 for deterministic output.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        # Keep explicit constructor key as an override; otherwise resolve from
        # environment dynamically on every request/check.
        self._api_key_override = api_key
        self.model = model

    def _resolve_api_key(self) -> str:
        """Resolve the API key at call-time to avoid stale env state."""
        _load_local_env()
        return (self._api_key_override or os.environ.get("GROQ_API_KEY", "")).strip()

    def is_available(self) -> bool:
        """Return True if a Groq API key is configured.

        This does a lightweight connectivity check when called with a network
        probe (used by the adapter on first availability check). Use
        `list_models()` for a stronger verification when needed.
        """
        return bool(self._resolve_api_key())

    def list_models(self) -> List[str]:
        """Return the list of available Groq models via the models endpoint."""
        if not self.is_available():
            return []
        try:
            api_key = self._resolve_api_key()
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=5,
            )
            if resp.status_code == 200:
                return [m["id"] for m in resp.json().get("data", [])]
        except Exception:
            pass
        return []

    def probe_connectivity(self, timeout: float = 2.0) -> bool:
        """Quickly probe the Groq models endpoint to verify API access.

        Returns True when the request succeeds within `timeout`, False otherwise.
        """
        if not self.is_available():
            return False
        try:
            api_key = self._resolve_api_key()
            resp = requests.get(
                "https://api.groq.com/openai/v1/models",
                headers={"Authorization": f"Bearer {api_key}"},
                timeout=timeout,
            )
            return resp.status_code == 200
        except Exception:
            return False

    def _best_model(self) -> str:
        """Return the best instruction-following model available on this account."""
        # Fixed preference order — ranked by JSON instruction-following quality
        PREFERRED = [
            "llama-3.3-70b-versatile",
            "meta-llama/llama-4-scout-17b-16e-instruct",
            "meta-llama/llama-4-maverick-17b-128e-instruct",
            "llama-3.1-8b-instant",
            "qwen/qwen3-32b",
        ]
        available = self.list_models()
        if not available:
            return self.model
        if self.model in available:
            return self.model
        for p in PREFERRED:
            if p in available:
                return p
        return available[0]

    def generate_raw(self, prompt: str, system: str = _SYSTEM_PROMPT) -> str:
        """
        Call Groq Chat Completions and return the assistant message text.
        temperature=0 enforces deterministic outputs.
        """
        if not self.is_available():
            raise RuntimeError(
                "GROQ_API_KEY is not set. "
                "Set it as an environment variable: GROQ_API_KEY=gsk_..."
            )

        # Truncate the prompt if it exceeds the allowed char budget
        if len(prompt) > MAX_PROMPT_CHARS:
            prompt = prompt[:MAX_PROMPT_CHARS] + "\n\n...[TRUNCATED]"

        payload = {
            "model": self._best_model(),
            "messages": [
                {"role": "system", "content": system},
                {"role": "user",   "content": prompt},
            ],
            "temperature": 0,
            "max_tokens":  256,
            "response_format": {"type": "json_object"},  # forces valid JSON output
        }
        api_key = self._resolve_api_key()
        resp = requests.post(
            GROQ_API_URL,
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type":  "application/json",
            },
            json=payload,
            timeout=REQUEST_TIMEOUT,
        )
        resp.raise_for_status()
        return resp.json()["choices"][0]["message"]["content"]

    def generate_json(self, prompt: str) -> Optional[Dict[str, Any]]:
        """Call Groq and extract a JSON dict from the response."""
        raw = self.generate_raw(prompt)
        return _extract_json(raw)


# ---------------------------------------------------------------------------
# JSON extraction + sanitization
# ---------------------------------------------------------------------------

def _extract_json(text: str) -> Optional[Dict[str, Any]]:
    """
    Try several strategies to extract a valid JSON object from LLM output.
    Returns None if all strategies fail.
    """
    # Strategy 1: direct parse (LLM returned clean JSON)
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        pass

    # Strategy 2: inside a ```json ... ``` block
    m = re.search(r"```(?:json)?\s*(\{.*?\})\s*```", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(1))
        except json.JSONDecodeError:
            pass

    # Strategy 3: find the outermost { ... } block
    m = re.search(r"\{.*\}", text, re.DOTALL)
    if m:
        try:
            return json.loads(m.group(0))
        except json.JSONDecodeError:
            pass

    return None


def _sanitize_instruction(raw: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate and normalise an LLM-generated instruction dict.
    Enforces spec: 5 exact keys, snake_case tasks, no index prefixes, valid module.
    """
    # module
    module = raw.get("module", "creator")
    if module not in ALLOWED_MODULES:
        module = "creator"

    # intent — snake_case
    intent = raw.get("intent", "process_request")
    if not isinstance(intent, str) or not intent.strip():
        intent = "process_request"
    intent = re.sub(r"\s+", "_", intent.strip().lower())

    # topic — strip leading action verbs
    topic = raw.get("topic", "")
    if not isinstance(topic, str) or not topic.strip():
        topic = "general topic"
    topic = re.sub(
        r"^(?:explain(?:\s+how\s+to)?|build|create|design|generate|analyze|"
        r"analyse|develop|implement|write|make|plan|describe|help(?:\s+me)?)\s+",
        "", topic.strip(), flags=re.IGNORECASE,
    ).strip() or topic.strip()

    # tasks — snake_case, strip any "0:" / "1." / "Step 1:" index prefixes
    # Also handle edge case where model returns tasks as a dict {0: ..., 1: ...}
    tasks_raw = raw.get("tasks", [])
    if isinstance(tasks_raw, dict):
        tasks_raw = list(tasks_raw.values())
    if not isinstance(tasks_raw, list) or len(tasks_raw) == 0:
        tasks_raw = ["analyze_request", "process_information", "generate_output"]
    cleaned = []
    for t in tasks_raw:
        t = str(t).strip()
        t = re.sub(r"^(?:step\s*)?\d+[.:\)\-]\s*", "", t, flags=re.IGNORECASE)
        t = t.strip()
        if not t:
            continue
        t = re.sub(r"[\s\-]+", "_", t.lower())
        t = re.sub(r"[^a-z0-9_]", "", t)
        t = re.sub(r"_+", "_", t).strip("_")
        if t:
            cleaned.append(t)
    tasks = cleaned[:7] or ["analyze_request", "process_information", "generate_output"]

    # output_format
    output_format = raw.get("output_format", "step_by_step_guide")
    if output_format not in ALLOWED_OUTPUT_FORMATS:
        output_format = "step_by_step_guide"

    return {
        "module":          module,
        "intent":          intent,
        "topic":           topic,
        "tasks":           tasks,
        "output_format":   output_format,
        "product_context": "creator_core",
    }


# ---------------------------------------------------------------------------
# High-level LLM Adapter
# ---------------------------------------------------------------------------

class LLMAdapter:
    """
    High-level adapter that uses the Groq API for dynamic instruction generation.

    Requires GROQ_API_KEY environment variable or api_key= constructor argument.
    Falls back gracefully when the key is missing or the API is unreachable.
    """

    def __init__(self, api_key: Optional[str] = None, model: str = DEFAULT_MODEL):
        # Always reload .env.local at adapter creation
        _load_local_env()
        self.client = GroqClient(api_key=api_key, model=model)
        self._available: Optional[bool] = None

    @property
    def available(self) -> bool:
        """Lazy-cached availability check (key present + API reachable)."""
        if self._available is None:
            # Check that an API key is configured and the service is reachable
            # with a short network probe to avoid falsely reporting availability
            # when the process started before env vars were set or the network
            # is unreachable.
            key_present = self.client.is_available()
            if not key_present:
                self._available = False
            else:
                self._available = self.client.probe_connectivity(timeout=2.0)
        return self._available

    def reset_availability_cache(self) -> None:
        """Force re-check on next access."""
        self._available = None

    def generate_instruction(self, prompt: str) -> Dict[str, Any]:
        """
        Use the Groq LLM to produce a structured instruction from `prompt`.
        Raises RuntimeError if GROQ_API_KEY is not configured.
        """
        if not self.available:
            raise RuntimeError(
                "Groq API key is not configured. "
                "Set GROQ_API_KEY environment variable to your key from console.groq.com"
            )

        raw = self.client.generate_json(prompt)
        if raw is None:
            raise ValueError("Groq did not return a parseable JSON object.")

        result = _sanitize_instruction(raw)
        # Echo the original user prompt (pre-truncation) as the first field
        result = {"prompt": prompt, **result}
        # product_context is always enforced here regardless of LLM output
        result["product_context"] = "creator_core"
        return result

    def generate_with_fallback(self, prompt: str, fallback_fn) -> Dict[str, Any]:
        """
        Try Groq first; on failure call fallback_fn(prompt) which must return
        a dict with the required instruction fields.
        """
        if self.available:
            try:
                return self.generate_instruction(prompt)
            except Exception:
                pass
        return fallback_fn(prompt)
