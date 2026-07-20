#!/usr/bin/env python3
"""
API Keys Checker for All 7 BHIV HR Platform Services
"""

import subprocess
import json

def get_container_env(container_name):
    """Get environment variables from Docker container"""
    try:
        result = subprocess.run(
            f"docker exec {container_name} env",
            shell=True, capture_output=True, text=True
        )
        if result.returncode == 0:
            env_vars = {}
            for line in result.stdout.strip().split('\n'):
                if '=' in line:
                    key, value = line.split('=', 1)
                    env_vars[key] = value
            return env_vars
        return {}
    except Exception as e:
        return {}

def main():
    """Check API keys for all services"""
    print("BHIV HR Platform - API Keys Summary")
    print("=" * 50)
    
    services = [
        ("Gateway Service", "docker-gateway-1"),
        ("Agent Service", "docker-agent-1"), 
        ("LangGraph Service", "docker-langgraph-1"),
        ("HR Portal", "docker-portal-1"),
        ("Client Portal", "docker-client_portal-1"),
        ("Candidate Portal", "docker-candidate_portal-1"),
        ("Database", "docker-db-1")
    ]
    
    api_key_fields = [
        'API_KEY_SECRET',
        'API_KEY', 
        'JWT_SECRET',
        'JWT_SECRET_KEY',
        'CANDIDATE_JWT_SECRET'
    ]
    
    for service_name, container_name in services:
        print(f"\n{service_name}:")
        print("-" * len(service_name))
        
        env_vars = get_container_env(container_name)
        
        if not env_vars:
            print("  [ERROR] Could not retrieve environment variables")
            continue
            
        found_keys = False
        for key_field in api_key_fields:
            if key_field in env_vars:
                value = env_vars[key_field]
                # Mask sensitive values but show structure
                if len(value) > 10:
                    masked_value = f"{value[:8]}...{value[-4:]}"
                else:
                    masked_value = value
                print(f"  {key_field}: {masked_value}")
                found_keys = True
        
        if not found_keys:
            print("  [INFO] No API keys configured")

if __name__ == "__main__":
    main()