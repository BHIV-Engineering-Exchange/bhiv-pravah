import uuid


def generate_execution_id():
    return f"exec_{uuid.uuid4().hex[:8]}"

 
def generate_trace_id():
    return f"trace_{uuid.uuid4().hex[:8]}"
