# Governance Code Packet

## Contents

| File | Purpose |
|------|---------|
| `app/services/mitra_control_plane_service.py` | Authority validation |
| `app/external/enforcement/` | Deterministic enforcement engine |
| `app/core/security.py` | JWT/API key auth, rate limiting |

## What Changed
- No changes to existing governance code
- Authority boundaries remain intact
- Constitutional assertions verified

## Why
- Governance is constitutional - must not be modified
- All new capabilities respect existing authority boundaries
