#!/usr/bin/env python3
import subprocess
import re

def get_env_vars(container):
    try:
        result = subprocess.run(f"docker exec {container} env", shell=True, capture_output=True, text=True)
        if result.returncode == 0:
            env_dict = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line and ('API' in line or 'JWT' in line):
                    key, value = line.split('=', 1)
                    env_dict[key] = value
            return env_dict
        return {}
    except:
        return {}

services = [
    ("Gateway", "docker-gateway-1"),
    ("Agent", "docker-agent-1"), 
    ("LangGraph", "docker-langgraph-1"),
    ("HR Portal", "docker-portal-1"),
    ("Client Portal", "docker-client_portal-1"),
    ("Candidate Portal", "docker-candidate_portal-1")
]

print("| Service | Port | API Key Variables | Values |")
print("|---------|------|-------------------|--------|")

ports = {"Gateway": 8000, "Agent": 9000, "LangGraph": 9001, "HR Portal": 8501, "Client Portal": 8502, "Candidate Portal": 8503}

for service_name, container in services:
    env_vars = get_env_vars(container)
    port = ports[service_name]
    
    if env_vars:
        keys = "<br>".join(env_vars.keys())
        values = "<br>".join([f"`{v}`" for v in env_vars.values()])
        print(f"| **{service_name}** | {port} | {keys} | {values} |")
    else:
        print(f"| **{service_name}** | {port} | None | None |")

print("| **Database** | 5432 | None | PostgreSQL credentials only |")