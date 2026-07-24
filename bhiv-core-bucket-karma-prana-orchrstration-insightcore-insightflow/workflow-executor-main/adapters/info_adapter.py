from typing import Dict, Any
from adapters.base import ExecutionAdapter


class InfoAdapter(ExecutionAdapter):
    def execute(self, payload: Dict[str, Any]) -> Dict[str, Any]:
        query = payload.get("query")

        if not query:
            return {
                "success": False,
                "error_code": "missing_info_query",
                "message": "query is required"
            }

        # Real data source hook placeholder

        return {
            "success": True,
            "query": query,
            "data": f"Live-ready info for '{query}'"
        }
