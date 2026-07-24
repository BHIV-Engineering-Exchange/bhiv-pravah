from fastapi import FastAPI
from fastapi.responses import JSONResponse

from .models import InboundRequest
from .enforcement import enforce
from .telemetry import emit
from .exceptions import EnforcementError
from .config import BRIDGE_VERSION

app = FastAPI()


@app.post("/ingest")
def ingest(req: InboundRequest):
    try:
        # Enforce security checks
        enforce(req.token, req.nonce)

        emit("ALLOW", "OK")
        return {
            "decision": "ALLOW",
            "reason": "OK",
            "version": BRIDGE_VERSION
        }

    except EnforcementError as e:
        emit("DENY", str(e))

        return JSONResponse(
            status_code=403,
            content={
                "decision": "DENY",
                "reason": str(e),   # ✅ FIXED
                "version": BRIDGE_VERSION
            }
        )

    except Exception:
        emit("DENY", "INTERNAL_ERROR")

        return JSONResponse(
            status_code=403,
            content={
                "decision": "DENY",
                "reason": "INTERNAL_ERROR",
                "version": BRIDGE_VERSION
            }
        )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.get("/metrics")
def metrics():
    return {"bridge_version": BRIDGE_VERSION}
