# TODO - Fix CI/CD Control Plane Health Check Timeout

## Root Cause
Port mismatch between workflow health checks (control-plane:7001, observer:8602)
and docker-compose.prod.yml defaults (7000, 8600), causing the control-plane
health check `curl http://$VM_IP:7001/api/health` to time out (exit 124).

## Steps
- [ ] Edit docker-compose.prod.yml: control-plane default port 7000 -> 7001
- [ ] Edit docker-compose.prod.yml: observer default port 8600 -> 8602
- [ ] Verify VM_IP GitHub secret is set to the VM public IP
- [ ] Push to main and re-run pipeline
