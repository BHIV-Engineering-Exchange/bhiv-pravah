#!/usr/bin/env python3
"""
BHIV HR Platform - Complete Endpoint Counter
Counts ALL endpoints from OpenAPI schemas and live services
"""

import asyncio
import httpx
import json
import re
from typing import Dict, List, Any

class EndpointCounter:
    def __init__(self):
        self.services = {
            "gateway": "http://localhost:8000",
            "agent": "http://localhost:9000", 
            "langgraph": "http://localhost:9001"
        }
        self.results = {}
        
    async def count_from_openapi(self, service_name: str, base_url: str) -> Dict[str, Any]:
        """Count endpoints from OpenAPI schema"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(f"{base_url}/openapi.json")
                if response.status_code == 200:
                    schema = response.json()
                    paths = schema.get("paths", {})
                    
                    endpoints = []
                    for path, methods in paths.items():
                        for method in methods.keys():
                            if method.upper() in ["GET", "POST", "PUT", "DELETE", "PATCH"]:
                                endpoints.append(f"{method.upper()} {path}")
                    
                    return {
                        "service": service_name,
                        "total_endpoints": len(endpoints),
                        "endpoints": endpoints,
                        "source": "openapi_schema"
                    }
        except Exception as e:
            print(f"❌ Failed to get OpenAPI for {service_name}: {e}")
            
        return {"service": service_name, "total_endpoints": 0, "endpoints": [], "source": "error"}
    
    async def count_from_code(self, service_name: str) -> Dict[str, Any]:
        """Count endpoints from source code"""
        endpoint_count = 0
        endpoints = []
        
        try:
            if service_name == "gateway":
                file_path = "c:\\BHIV HR PLATFORM\\services\\gateway\\app\\main.py"
            elif service_name == "agent":
                file_path = "c:\\BHIV HR PLATFORM\\services\\agent\\app.py"
            elif service_name == "langgraph":
                file_path = "c:\\BHIV HR PLATFORM\\services\\langgraph\\app\\main.py"
            else:
                return {"service": service_name, "total_endpoints": 0, "endpoints": [], "source": "unknown"}
            
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
                
                # Find all endpoint decorators with their paths
                patterns = [
                    (r'@app\.get\(["\']([^"\']+)["\']', "GET"),
                    (r'@app\.post\(["\']([^"\']+)["\']', "POST"),
                    (r'@app\.put\(["\']([^"\']+)["\']', "PUT"),
                    (r'@app\.delete\(["\']([^"\']+)["\']', "DELETE"),
                    (r'@app\.patch\(["\']([^"\']+)["\']', "PATCH"),
                    (r'@app\.websocket\(["\']([^"\']+)["\']', "WEBSOCKET")
                ]
                
                for pattern, method in patterns:
                    matches = re.findall(pattern, content)
                    for path in matches:
                        endpoints.append(f"{method} {path}")
                        endpoint_count += 1
                
        except Exception as e:
            print(f"❌ Error reading code for {service_name}: {e}")
            
        return {
            "service": service_name,
            "total_endpoints": endpoint_count,
            "endpoints": endpoints,
            "source": "source_code"
        }
    
    async def get_service_info(self, service_name: str, base_url: str) -> Dict[str, Any]:
        """Get service information from root endpoint"""
        try:
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(base_url)
                if response.status_code == 200:
                    data = response.json()
                    return {
                        "service": service_name,
                        "claimed_endpoints": data.get("endpoints", 0),
                        "version": data.get("version", "unknown"),
                        "status": data.get("status", "unknown"),
                        "source": "service_info"
                    }
        except Exception as e:
            print(f"❌ Failed to get service info for {service_name}: {e}")
            
        return {"service": service_name, "claimed_endpoints": 0, "source": "error"}
    
    async def run_complete_count(self):
        """Run complete endpoint counting"""
        print("BHIV HR Platform - Complete Endpoint Counter")
        print("=" * 60)
        
        total_openapi = 0
        total_code = 0
        total_claimed = 0
        
        for service_name, base_url in self.services.items():
            print(f"\nAnalyzing {service_name.upper()} Service...")
            
            # Count from OpenAPI schema
            openapi_result = await self.count_from_openapi(service_name, base_url)
            
            # Count from source code
            code_result = await self.count_from_code(service_name)
            
            # Get service claimed count
            info_result = await self.get_service_info(service_name, base_url)
            
            # Store results
            self.results[service_name] = {
                "openapi": openapi_result,
                "code": code_result,
                "claimed": info_result
            }
            
            # Print results
            print(f"  OpenAPI Schema: {openapi_result['total_endpoints']} endpoints")
            print(f"  Source Code: {code_result['total_endpoints']} endpoints")
            print(f"  Service Claims: {info_result.get('claimed_endpoints', 0)} endpoints")
            
            # Add to totals
            total_openapi += openapi_result['total_endpoints']
            total_code += code_result['total_endpoints']
            total_claimed += info_result.get('claimed_endpoints', 0)
            
            # Show discrepancies
            if openapi_result['total_endpoints'] != code_result['total_endpoints']:
                print(f"  WARNING: Discrepancy: OpenAPI vs Code ({openapi_result['total_endpoints']} vs {code_result['total_endpoints']})")
        
        # Print summary
        print("\n" + "=" * 60)
        print("COMPLETE ENDPOINT COUNT SUMMARY")
        print("=" * 60)
        print(f"Total from OpenAPI Schemas: {total_openapi}")
        print(f"Total from Source Code: {total_code}")
        print(f"Total Claimed by Services: {total_claimed}")
        print(f"Documentation Claims: 111 endpoints")
        
        # Determine most accurate count
        most_accurate = max(total_openapi, total_code, total_claimed)
        print(f"\nMOST ACCURATE COUNT: {most_accurate} endpoints")
        
        if most_accurate != 89:
            difference = most_accurate - 89
            print(f"Documentation Adjustment Needed: {difference:+d} endpoints")
        
        # Detailed breakdown
        print(f"\nDETAILED BREAKDOWN:")
        for service_name, results in self.results.items():
            openapi_count = results['openapi']['total_endpoints']
            code_count = results['code']['total_endpoints']
            claimed_count = results['claimed'].get('claimed_endpoints', 0)
            
            print(f"\n{service_name.upper()} Service:")
            print(f"  OpenAPI: {openapi_count} | Code: {code_count} | Claimed: {claimed_count}")
            
            # Show some actual endpoints
            if results['openapi']['endpoints']:
                print(f"  Sample endpoints:")
                for endpoint in results['openapi']['endpoints'][:5]:
                    print(f"    - {endpoint}")
                if len(results['openapi']['endpoints']) > 5:
                    print(f"    ... and {len(results['openapi']['endpoints']) - 5} more")
        
        return {
            "total_openapi": total_openapi,
            "total_code": total_code,
            "total_claimed": total_claimed,
            "most_accurate": most_accurate,
            "documentation_claims": 111,
            "adjustment_needed": most_accurate - 111
        }

async def main():
    counter = EndpointCounter()
    results = await counter.run_complete_count()
    
    # Save detailed results
    with open("COMPLETE_ENDPOINT_COUNT.json", "w") as f:
        json.dump({
            "summary": results,
            "detailed_results": counter.results,
            "timestamp": "2026-01-22"
        }, f, indent=2)
    
    print(f"\nDetailed results saved to: COMPLETE_ENDPOINT_COUNT.json")

if __name__ == "__main__":
    asyncio.run(main())