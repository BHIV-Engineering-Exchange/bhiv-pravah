import sys
import os
import uuid
import time

sys.path.insert(0, os.path.abspath("."))

try:
    from integration_bridge import BHIVIntegrationBridge
    bridge = BHIVIntegrationBridge()
    # If instantiation succeeds, call _report_to_pravah
    print("Instantiated BHIVIntegrationBridge, triggering _report_to_pravah...")
    trace_id = f"trace-{uuid.uuid4().hex[:12]}"
    bridge._report_to_pravah(trace_id, "success", 1250.5)
    print("Integrator telemetry triggered!")
    time.sleep(3)  # wait for thread to finish
except Exception as e:
    print("Failed to instantiate BHIVIntegrationBridge, trying mock execution:", e)
    try:
        from integration_bridge import BHIVIntegrationBridge
        # Mock class/instance just to get the function
        bridge = object.__new__(BHIVIntegrationBridge)
        trace_id = f"trace-{uuid.uuid4().hex[:12]}"
        bridge._report_to_pravah(trace_id, "success", 850.2)
        print("Mocked integrator telemetry triggered for trace:", trace_id)
        time.sleep(3)
    except Exception as err:
        print("Verification failed:", err)
        sys.exit(1)
