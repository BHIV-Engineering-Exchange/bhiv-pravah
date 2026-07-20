#!/usr/bin/env python3
"""
Verification Script for AI-CRM Observability
Instantiates the TelemetryLayer and emits mock SETU execution events to test signing
and out-of-band propagation to the Pravah Bhiv control plane and observer.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add backend directory to Python path
backend_dir = Path(__file__).resolve().parent
sys.path.append(str(backend_dir))

from setu.mongo_store import MongoSetuStore
from setu.telemetry_layer import TelemetryLayer

async def main():
    print("[START] Starting AI-CRM Observability Verification...")
    
    # Initialize components
    try:
        store = MongoSetuStore()
        telemetry = TelemetryLayer(store)
        print("[SUCCESS] MongoDB/SQLite Store and TelemetryLayer instantiated successfully")
    except Exception as e:
        print(f"[ERROR] Failed to instantiate components: {e}")
        return

    # Create mock execution event
    execution = {
        "execution_id": "test-exec-111",
        "trace_id": "test-trace-999",
        "tenant_id": "tenant-dev",
        "timestamp": None,
        "source_system": "crm-verification"
    }
    
    print("[SEND] Emitting mock 'execution_started' telemetry event...")
    try:
        started_event = await telemetry.emit_execution_started(
            execution=execution,
            details={"subsystem": "test-verifier", "message": "Verification starting"}
        )
        print(f"[SUCCESS] Emitted execution_started event: {started_event.get('execution_id')}")
    except Exception as e:
        print(f"[ERROR] Failed to emit execution_started: {e}")
        
    # Wait a bit
    print("[WAIT] Simulating workload...")
    await asyncio.sleep(0.5)

    print("[SEND] Emitting mock 'execution_completed' telemetry event...")
    try:
        completed_event = await telemetry.emit_execution_completed(
            execution=execution,
            details={"subsystem": "test-verifier", "duration_ms": 500, "message": "Verification completed"}
        )
        print(f"[SUCCESS] Emitted execution_completed event: {completed_event.get('execution_id')}")
    except Exception as e:
        print(f"[ERROR] Failed to emit execution_completed: {e}")

    # Allow background network tasks to flush out-of-band requests
    print("[WAIT] Waiting for out-of-band telemetry request to finish...")
    await asyncio.sleep(2.0)
    print("[COMPLETE] Verification run completed! Check the Observer dashboard (http://localhost:8600).")

if __name__ == "__main__":
    asyncio.run(main())
