# Node Interruption Results

**Supersedes:** prior `04_validation/node_interruption_results.md` (rate-limit only)  
**Generated:** 2026-07-07T12:54:35.707035+00:00  
**Status:** PASS

## Test

SIGKILL BHIV Core before pipeline execution (`taskkill /F`), run pipeline through CET/Sarathi/Gate, confirm clean failure before A3.

| Field | Value |
|-------|-------|
| Trace ID | `rec_3b2c0c81b9` |
| BHIV PID killed | `None` |
| Kill command | `` |
| Pipeline status | `500` |
| Bucket types after failure | `['authority', 'blueprint', 'contract', 'gate', 'instruction']` |
| Clean failure | `True` |

### Pipeline response excerpt

```
{"detail":"HTTPConnectionPool(host='127.0.0.1', port=8001): Max retries exceeded with url: /core (Caused by NewConnectionError('<urllib3.connection.HTTPConnection object at 0x000002099BD7F8A0>: Failed to establish a new connection: [WinError 10061] No connection could be made because the target machine actively refused it'))"}
```
