import os
import uvicorn

if __name__ == "__main__":
    host = os.getenv("UNIGURU_HOST", "0.0.0.0")
    port = int(os.getenv("UNIGURU_PORT", "8000"))
    reload_enabled = os.getenv("UNIGURU_RELOAD", "true").lower() in {"1", "true", "yes", "on"}

    uvicorn.run(
        "service.api:app",
        host=host,
        port=port,
        reload=reload_enabled,
    )