#!/usr/bin/env python3
"""
Generate OpenAPI specification for the AI Agent Logistics API
"""

import json
from api_app import app

def generate_openapi_spec():
    """Generate OpenAPI 3.0 specification from FastAPI app"""
    try:
        # Get the OpenAPI schema from FastAPI
        openapi_schema = app.openapi()

        # Save to docs/ directory
        with open('docs/openapi_spec.json', 'w') as f:
            json.dump(openapi_schema, f, indent=2)

        # Also save as YAML for better readability
        try:
            import yaml
            with open('docs/openapi_spec.yaml', 'w') as f:
                yaml.dump(openapi_schema, f, default_flow_style=False)
        except ImportError:
            print("PyYAML not available, skipping YAML generation")

        print("OpenAPI specification generated successfully!")
        print("Files created:")
        print("   - docs/openapi_spec.json")
        print("   - docs/openapi_spec.yaml (if PyYAML available)")

        return True
    except Exception as e:
        print(f"Error generating OpenAPI spec: {e}")
        return False

if __name__ == "__main__":
    generate_openapi_spec()