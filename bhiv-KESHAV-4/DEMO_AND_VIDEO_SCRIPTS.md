# KESHAV Demo & Video Script

## 1. Demo Video (Recording Guide)

1. Open a split terminal (Left: server, Right: client).
2. On Left: run `python api.py`. Show the server start up.
3. On Right: run `curl http://localhost:5000/health`. Show the `{"status": "OK"}`.
4. On Right: run `curl -X POST http://localhost:5000/analyze -H "Content-Type: application/json" -d @sample_input.json`. 
5. Show the JSON response returning a `UNBLOCK_DEPENDENCY` signal and a `HIGH` severity.
6. On Right: run `python tantra_wiring_proof.py`. Show the 54 assertions flying by and passing.
7. On Right: run `python replay_determinism_proof.py`. Show the hash equality checks passing.

## 2. Live Walkthrough Agenda

1. **The Goal:** KESHAV is a pure dependency intelligence engine.
2. **The Architecture:** Explain how `analyzer/analyze_blockage.py` replaced `app/engine.py`.
3. **The Proof:** Run `python -m pytest tests/` to show 100% coverage instantly.
4. **The Flow:** Walk through `tantra_wiring_proof.py` to explain how KESHAV passes output seamlessly to RAJYA, Sarathi, and Core without mutation.
5. **The Hardening:** Run `python production_hardening_proof.py` to prove failure resistance.

## 3. Deployment Recording

1. Show Docker build: `docker build -t keshav:latest .`
2. Show K8s apply: `kubectl apply -f k8s-deployment.yaml`
3. Show Pods running: `kubectl get pods -n keshav`
4. Tail logs to show readiness: `kubectl logs -n keshav -l app=keshav`
