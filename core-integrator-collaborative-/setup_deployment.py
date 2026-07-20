"""
Quick Deployment Script
=======================
Deploy BHIV services independently with custom URLs
"""

import os
import sys
from pathlib import Path

def create_env_file(service_name: str, config: dict):
    """Create .env file for a service"""
    env_path = Path(__file__).parent / f".env.{service_name}"
    
    with open(env_path, 'w') as f:
        f.write(f"# {service_name.upper()} Service Configuration\n")
        f.write(f"# Generated for independent deployment\n\n")
        
        for key, value in config.items():
            f.write(f"{key}={value}\n")
    
    print(f"[OK] Created {env_path}")
    return env_path


def main():
    print("\n" + "="*70)
    print("BHIV INDEPENDENT DEPLOYMENT CONFIGURATION")
    print("="*70)
    
    print("\nThis script will create environment files for each service.")
    print("You can then deploy each service on separate servers.\n")
    
    # Prompt Runner Config
    print("\n[1/5] Prompt Runner Configuration")
    prompt_runner_host = input("Enter Prompt Runner host (default: 127.0.0.1): ").strip() or "127.0.0.1"
    prompt_runner_port = input("Enter Prompt Runner port (default: 8003): ").strip() or "8003"
    groq_api_key = input("Enter GROQ API Key: ").strip()
    
    create_env_file("prompt_runner", {
        "PORT": prompt_runner_port,
        "GROQ_API_KEY": groq_api_key,
        "CREATOR_CORE_URL": f"http://127.0.0.1:8000"  # Will be updated later
    })
    
    # Creator Core Config
    print("\n[2/5] Creator Core Configuration")
    creator_core_host = input("Enter Creator Core host (default: 127.0.0.1): ").strip() or "127.0.0.1"
    creator_core_port = input("Enter Creator Core port (default: 8000): ").strip() or "8000"
    
    create_env_file("creator_core", {
        "PORT": creator_core_port,
        "GROQ_API_KEY": groq_api_key
    })
    
    # BHIV Core Config
    print("\n[3/5] BHIV Core Configuration")
    bhiv_core_host = input("Enter BHIV Core host (default: 127.0.0.1): ").strip() or "127.0.0.1"
    bhiv_core_port = input("Enter BHIV Core port (default: 8001): ").strip() or "8001"
    use_mongodb = input("Use MongoDB? (y/n, default: n): ").strip().lower() == 'y'
    
    bhiv_config = {
        "PORT": bhiv_core_port,
        "USE_MONGODB": "true" if use_mongodb else "false",
        "DB_PATH": "data/context.db"
    }
    
    if use_mongodb:
        mongo_url = input("Enter MongoDB connection string: ").strip()
        mongo_db = input("Enter MongoDB database name (default: bhiv_production): ").strip() or "bhiv_production"
        bhiv_config["MONGODB_CONNECTION_STRING"] = mongo_url
        bhiv_config["MONGODB_DATABASE_NAME"] = mongo_db
    
    create_env_file("bhiv_core", bhiv_config)
    
    # Bucket Config
    print("\n[4/5] Bucket Configuration")
    bucket_host = input("Enter Bucket host (default: 127.0.0.1): ").strip() or "127.0.0.1"
    bucket_port = input("Enter Bucket port (default: 8005): ").strip() or "8005"
    
    create_env_file("bucket", {
        "PORT": bucket_port,
        "STORAGE_PATH": "data/artifacts"
    })
    
    # Integration Bridge Config
    print("\n[5/5] Integration Bridge Configuration")
    bridge_host = input("Enter Integration Bridge host (default: 127.0.0.1): ").strip() or "127.0.0.1"
    bridge_port = input("Enter Integration Bridge port (default: 8004): ").strip() or "8004"
    
    create_env_file("integration_bridge", {
        "PORT": bridge_port,
        "PROMPT_RUNNER_URL": f"http://{prompt_runner_host}:{prompt_runner_port}",
        "CREATOR_CORE_URL": f"http://{creator_core_host}:{creator_core_port}",
        "BHIV_CORE_URL": f"http://{bhiv_core_host}:{bhiv_core_port}",
        "BUCKET_URL": f"http://{bucket_host}:{bucket_port}"
    })
    
    # Summary
    print("\n" + "="*70)
    print("DEPLOYMENT FILES CREATED")
    print("="*70)
    print("\nEnvironment files created:")
    print("  - .env.prompt_runner")
    print("  - .env.creator_core")
    print("  - .env.bhiv_core")
    print("  - .env.bucket")
    print("  - .env.integration_bridge")
    
    print("\n" + "="*70)
    print("SERVICE URLS")
    print("="*70)
    print(f"  Prompt Runner:    http://{prompt_runner_host}:{prompt_runner_port}")
    print(f"  Creator Core:     http://{creator_core_host}:{creator_core_port}")
    print(f"  BHIV Core:        http://{bhiv_core_host}:{bhiv_core_port}")
    print(f"  Bucket:           http://{bucket_host}:{bucket_port}")
    print(f"  Integration Bridge: http://{bridge_host}:{bridge_port}")
    
    print("\n" + "="*70)
    print("DEPLOYMENT COMMANDS")
    print("="*70)
    print("\nDeploy each service using:")
    print("\n  # Prompt Runner")
    print(f"  export $(cat .env.prompt_runner | xargs)")
    print("  # Start Prompt Runner from its own deployment or IDE; set PROMPT_RUNNER_URL to the service URL")
    print("\n  # Creator Core")
    print(f"  export $(cat .env.creator_core | xargs)")
    print("  python creator-core/Core-Integrator-Sprint-1.1/main.py")
    print("\n  # BHIV Core")
    print(f"  export $(cat .env.bhiv_core | xargs)")
    print("  python main.py")
    print("\n  # Bucket")
    print(f"  export $(cat .env.bucket | xargs)")
    print("  python bhiv_bucket.py")
    print("\n  # Integration Bridge")
    print(f"  export $(cat .env.integration_bridge | xargs)")
    print("  python integration_bridge_v2.py")
    
    print("\n" + "="*70)
    print("TEST COMMANDS")
    print("="*70)
    print("\nTest full pipeline:")
    print(f"  curl -X POST http://{bridge_host}:{bridge_port}/pipeline/execute \\")
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"prompt": "Design a residential building"}\'')
    print("\nCheck health:")
    print(f"  curl http://{bridge_host}:{bridge_port}/pipeline/health")
    print("\n" + "="*70 + "\n")


if __name__ == "__main__":
    main()
