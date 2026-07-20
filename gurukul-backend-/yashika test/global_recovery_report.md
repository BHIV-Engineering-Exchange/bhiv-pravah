# Global Recovery Report - Simulation Results

This report documents the self-healing behavior of the entire Gurukul ecosystem during simulated production failure events.

## 1. Cross-Service Dependency Failure
- **Scenario**: EMS Backend goes down while Core Backend stays up.
- **Discovery**: Frontend client-side watchdog detected EMS 500 errors.
- **Recovery**: Core Backend remained unaffected (Sovereignty). EMS Watchdog successfully restarted the service once PostgreSQL became available.

## 2. Global Startup Collision
- **Scenario**: Attempting to start Core and EMS on the same port.
- **Discovery**: Core Watchdog reported `Port Already In Use`.
- **Recovery**: Script fixed assigning 3001 to Core and 3002 to EMS. Deterministic failure prevented silent port stealing.

## 3. High-Load Database Pressure
- **Scenario**: Saturating SQL connection pools for Core + EMS.
- **Discovery**: `/health` reported `unhealthy: pool timeout`.
- **Recovery**: Self-healing connection pooling (Day 3 logic) successfully recycled idle handles without crashing the app.

## Summary
The unified system is robust against cascading failures.
