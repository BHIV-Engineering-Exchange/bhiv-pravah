from abc import ABC, abstractmethod
from typing import Dict, Any, List, Optional
from .memory import ContextMemory
from ..utils.noopur_client import NoopurClient
from config.config import INTEGRATOR_USE_NOOPUR
import asyncio
import concurrent.futures

try:
    from .mongodb_adapter import MongoDBAdapter, PYMONGO_AVAILABLE
    MONGODB_AVAILABLE = PYMONGO_AVAILABLE
except ImportError:
    MongoDBAdapter = None
    MONGODB_AVAILABLE = False


def _run_async(coro):
    """Run an async coroutine safely regardless of whether an event loop is running."""
    try:
        loop = asyncio.get_running_loop()
    except RuntimeError:
        loop = None

    if loop and loop.is_running():
        # We are inside a running loop (e.g. called from sync code spawned by FastAPI).
        # Use a thread executor to avoid nesting event loops.
        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as pool:
            future = pool.submit(asyncio.run, coro)
            return future.result()
    else:
        return asyncio.run(coro)


class MemoryAdapter(ABC):
    @abstractmethod
    def store_interaction(self, user_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        pass

    @abstractmethod
    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        pass

    @abstractmethod
    def get_context(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        pass


class SQLiteAdapter(MemoryAdapter):
    def __init__(self, db_path: str = "data/context.db"):
        self._mem = ContextMemory(db_path)

    def store_interaction(self, user_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        self._mem.store_interaction(user_id, request_data, response_data)

    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        return self._mem.get_user_history(user_id)

    def get_context(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        return self._mem.get_context(user_id, limit)


class RemoteNoopurAdapter(MemoryAdapter):
    """Adapter that reads context from Noopur backend for pre-warming.

    This adapter is read-heavy: it will fetch related_context via Noopur's /generate or /history endpoints.
    store_interaction is implemented as a best-effort no-op (could be extended to forward logs).
    """

class RemoteNoopurAdapter(MemoryAdapter):
    """Adapter that reads context from Noopur backend for pre-warming.

    This adapter is read-heavy: it will fetch related_context via Noopur's /generate or /history endpoints.
    store_interaction is implemented as a best-effort no-op (could be extended to forward logs).
    """

    def __init__(self, base_url: Optional[str] = None):
        # Allow overriding base_url for testing or local noopur instance
        if INTEGRATOR_USE_NOOPUR:
            if base_url:
                self.client = NoopurClient(base_url)
            else:
                self.client = NoopurClient()
        else:
            self.client = None

    def store_interaction(self, user_id: str, request_data: Dict[str, Any], response_data: Dict[str, Any]):
        # Forward certain interaction types to Noopur for telemetry/feedback
        if not self.client:
            return None

        async def _store():
            try:
                # If this is a creator generation (has 'data' with prompt/topic), forward as a create
                if request_data.get("module") == "creator":
                    payload = {}
                    # try to map common fields
                    payload["prompt"] = request_data.get("data", {}).get("prompt") or request_data.get("data", {}).get("topic")
                    # include user_id for traceability if supported by Noopur
                    payload["user_id"] = user_id
                    # Only send minimal payload to avoid leaking internal fields
                    try:
                        await self.client.generate(payload)
                    except Exception:
                        # swallow remote errors
                        pass

                # If this looks like feedback (response_data contains score or explicit feedback), forward to /feedback
                if request_data.get("intent") in ("feedback",) or isinstance(response_data.get("result"), dict) and "score" in response_data.get("result", {}):
                    fb = {}
                    # map possible shapes
                    if "id" in response_data.get("result", {}):
                        fb["generation_id"] = response_data["result"]["id"]
                    if "score" in response_data.get("result", {}):
                        # convert score into a command-like string for Noopur API (+/-)
                        fb["command"] = str(response_data["result"]["score"])
                    try:
                        if fb:
                            await self.client.feedback(fb)
                    except Exception:
                        pass

            except Exception:
                # ensure we never raise from the adapter forwarder
                return None

        # Run the async operation
        try:
            _run_async(_store())
        except Exception:
            pass

        return None

    def get_user_history(self, user_id: str) -> List[Dict[str, Any]]:
        # Try fetching history from Noopur and map to local shape
        if not self.client:
            return []
        
        async def _get_history():
            try:
                items = await self.client.history()
                # API returns a list of generations: {id, text, score, created_at}
                mapped = [
                    {
                        "module": "creator",
                        "timestamp": it.get("created_at") or it.get("timestamp"),
                        "request": {"prompt": None},
                        "response": {"generated_text": it.get("text"), "score": it.get("score"), "id": it.get("id")}
                    }
                    for it in items
                ]
                # Sort by timestamp desc, fallback to id desc
                mapped.sort(key=lambda x: (x.get("timestamp") or "", x["response"].get("id") or 0), reverse=True)
                return mapped
            except Exception:
                return []

        try:
            return _run_async(_get_history())
        except Exception:
            return []

    def get_context(self, user_id: str, limit: int = 3) -> List[Dict[str, Any]]:
        # Fetch recent generations from Noopur and return top-N as context
        if not self.client:
            return []
        
        async def _get_context():
            try:
                items = await self.client.history()
                mapped = [
                    {
                        "module": "creator",
                        "timestamp": it.get("created_at") or it.get("timestamp"),
                        "request": {"prompt": None},
                        "response": {"generated_text": it.get("text"), "score": it.get("score"), "id": it.get("id")}
                    }
                    for it in items
                ]
                mapped.sort(key=lambda x: (x.get("timestamp") or "", x["response"].get("id") or 0), reverse=True)
                return mapped[:limit]
            except Exception:
                return []

        try:
            return _run_async(_get_context())
        except Exception:
            return []
