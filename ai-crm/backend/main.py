"""Minimal FastAPI app exposing inventory and returns data from Excel."""

from fastapi import FastAPI, HTTPException

from excel_to_json_pipeline import load_inventory, load_returns

app = FastAPI(title="ERP Ingestion API", version="0.1.0")


@app.get("/get_inventory_status")
def get_inventory_status():
    """
    Return the latest inventory snapshot as JSON.
    Reads Excel on every request to keep behavior simple for now.
    """
    try:
        return load_inventory()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load inventory: {exc}")


@app.get("/get_returns")
def get_returns():
    """Return normalized returns data as JSON."""
    try:
        return load_returns()
    except FileNotFoundError as exc:
        raise HTTPException(status_code=404, detail=str(exc))
    except Exception as exc:
        raise HTTPException(status_code=500, detail=f"Failed to load returns: {exc}")
