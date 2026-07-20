# Determinism Report

Request: `{"horizon": "intraday", "symbols": ["TCS.NS"]}`

Runs executed: 3
Same structure/schema: PASS
Random/missing fields: PASS
Controlled variance: PASS (price stable in validation stub; real-time price is the only allowed production variance)

Normalized schema:
```json
{
  "metadata": {
    "count": "int",
    "horizon": "str",
    "risk_profile": "str"
  },
  "predictions": [
    {
      "action": "str",
      "confidence": "float",
      "current_price": "float",
      "data_status": {
        "data_freshness_seconds": "int",
        "data_source": "str",
        "market_context": "str"
      },
      "horizon": "str",
      "predicted_price": "float",
      "symbol": "str"
    }
  ]
}
```