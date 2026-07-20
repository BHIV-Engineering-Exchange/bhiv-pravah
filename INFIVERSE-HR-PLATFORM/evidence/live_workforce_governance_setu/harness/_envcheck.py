import importlib.util as u
mods = ["fastapi", "httpx", "motor", "mongomock_motor", "mongomock", "pytest", "jwt", "pydantic", "bson", "starlette"]
for m in mods:
    print(m, bool(u.find_spec(m)))
import sys
print("python", sys.version)
