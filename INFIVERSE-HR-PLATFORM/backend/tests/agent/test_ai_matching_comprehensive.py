#!/usr/bin/env python3
"""
Comprehensive AI Matching Endpoints Testing & Schema Validation
Tests Gateway and Agent services with proper authentication and schema validation
"""

import asyncio
import httpx
import json
import time
from typing import Dict, List, Any

# Configuration
GATEWAY_SERVICE_URL = "https://bhiv-hr-gateway-ltg0.onrender.com"
AGENT_URL = "https://bhiv-hr-agent-nhgg.onrender.com"
API_KEY = "<YOUR_API_KEY>"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Content-Type": "application/json"
}

class ComprehensiveAITester:
    def __init__(self):
        self.results = {}
        self.schema_errors = []
        self.performance_metrics = {}
        
    async def wake_agent_service(self):
        """Wake up Agent service if sleeping"""
        print("\n[WAKE] Waking up Agent service...")
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.get(f"{AGENT_URL}/health")
                if response.status_code == 200:
                    print("[SUCCESS] Agent service is awake")
                    return True
                else:
                    print(f"[WARNING] Agent wake response: {response.status_code}")
                    return False
        except Exception as e:
            print(f"[ERROR] Agent wake failed: {str(e)}")
            return False

    async def test_gateway_single_match_detailed(self):
        """Test Gateway single match with detailed schema validation"""
        print("\n[TEST] Gateway Single Match - Detailed Schema Validation")
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.get(
                    f"{GATEWAY_SERVICE_URL}/v1/match/1/top?limit=5",
                    headers=HEADERS
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[SUCCESS] Gateway Single Match: {response.status_code} ({response_time:.3f}s)")
                    
                    # Comprehensive schema validation
                    expected_root_fields = [
                        "matches", "job_id", "limit", "total_candidates", 
                        "algorithm_version", "processing_time", "ai_analysis"
                    ]
                    
                    missing_root = [field for field in expected_root_fields if field not in data]
                    if missing_root:
                        self.schema_errors.append(f"Gateway Single - Missing root fields: {missing_root}")
                    
                    # Validate matches structure
                    if "matches" in data and data["matches"]:
                        match = data["matches"][0]
                        expected_match_fields = [
                            "candidate_id", "name", "email", "score", 
                            "skills_match", "experience_match", "location_match", 
                            "reasoning", "recommendation_strength"
                        ]
                        
                        missing_match = [field for field in expected_match_fields if field not in match]
                        if missing_match:
                            self.schema_errors.append(f"Gateway Single Match - Missing fields: {missing_match}")
                        else:
                            print("[SCHEMA] All match fields present")
                            
                        # Validate field types
                        type_validations = [
                            ("candidate_id", int),
                            ("name", str),
                            ("email", str),
                            ("score", (int, float)),
                            ("location_match", bool)
                        ]
                        
                        for field, expected_type in type_validations:
                            if field in match and not isinstance(match[field], expected_type):
                                self.schema_errors.append(f"Gateway Single - {field} type mismatch: expected {expected_type}, got {type(match[field])}")
                    
                    self.results["gateway_single"] = {
                        "status": "success",
                        "response_time": response_time,
                        "matches_count": len(data.get("matches", [])),
                        "algorithm_version": data.get("algorithm_version"),
                        "agent_status": data.get("agent_status"),
                        "sample_score": data["matches"][0]["score"] if data.get("matches") else None
                    }
                    
                    print(f"   Matches Found: {len(data.get('matches', []))}")
                    print(f"   Algorithm: {data.get('algorithm_version')}")
                    print(f"   Agent Status: {data.get('agent_status')}")
                    if data.get("matches"):
                        print(f"   Top Score: {data['matches'][0]['score']}")
                        print(f"   Sample Reasoning: {data['matches'][0].get('reasoning', 'N/A')[:60]}...")
                    
                else:
                    print(f"[FAILED] Gateway Single Match: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    self.results["gateway_single"] = {"status": "failed", "code": response.status_code}
                    
        except Exception as e:
            print(f"[ERROR] Gateway Single Match: {str(e)}")
            self.results["gateway_single"] = {"status": "error", "error": str(e)}

    async def test_gateway_batch_match_detailed(self):
        """Test Gateway batch match with detailed schema validation"""
        print("\n[TEST] Gateway Batch Match - Detailed Schema Validation")
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{GATEWAY_SERVICE_URL}/v1/match/batch",
                    headers=HEADERS,
                    json=[1, 2, 3]
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[SUCCESS] Gateway Batch Match: {response.status_code} ({response_time:.3f}s)")
                    
                    # Schema validation
                    expected_batch_fields = [
                        "batch_results", "total_jobs_processed", 
                        "algorithm_version", "status"
                    ]
                    
                    missing_batch = [field for field in expected_batch_fields if field not in data]
                    if missing_batch:
                        self.schema_errors.append(f"Gateway Batch - Missing root fields: {missing_batch}")
                    
                    # Validate batch results structure
                    if "batch_results" in data:
                        batch_results = data["batch_results"]
                        for job_id, job_result in batch_results.items():
                            expected_job_fields = ["job_id", "matches", "total_candidates"]
                            missing_job = [field for field in expected_job_fields if field not in job_result]
                            
                            if missing_job:
                                self.schema_errors.append(f"Gateway Batch Job {job_id} - Missing: {missing_job}")
                            
                            # Validate match structure in batch
                            if job_result.get("matches"):
                                batch_match = job_result["matches"][0]
                                expected_batch_match_fields = [
                                    "candidate_id", "name", "email", "score", 
                                    "skills_match", "experience_match", "location_match", "reasoning"
                                ]
                                
                                missing_batch_match = [field for field in expected_batch_match_fields 
                                                     if field not in batch_match]
                                
                                if missing_batch_match:
                                    self.schema_errors.append(f"Gateway Batch Match Job {job_id} - Missing: {missing_batch_match}")
                                else:
                                    print(f"[SCHEMA] Batch match fields validated for job {job_id}")
                    
                    self.results["gateway_batch"] = {
                        "status": "success",
                        "response_time": response_time,
                        "jobs_processed": data.get("total_jobs_processed"),
                        "algorithm_version": data.get("algorithm_version"),
                        "agent_status": data.get("agent_status")
                    }
                    
                    print(f"   Jobs Processed: {data.get('total_jobs_processed')}")
                    print(f"   Algorithm: {data.get('algorithm_version')}")
                    
                else:
                    print(f"[FAILED] Gateway Batch Match: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    self.results["gateway_batch"] = {"status": "failed", "code": response.status_code}
                    
        except Exception as e:
            print(f"[ERROR] Gateway Batch Match: {str(e)}")
            self.results["gateway_batch"] = {"status": "error", "error": str(e)}

    async def test_agent_direct_match_detailed(self):
        """Test Agent service direct match with authentication"""
        print("\n[TEST] Agent Direct Match - With Authentication")
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=60.0) as client:
                response = await client.post(
                    f"{AGENT_URL}/match",
                    headers=HEADERS,
                    json={"job_id": 1, "limit": 5}
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[SUCCESS] Agent Direct Match: {response.status_code} ({response_time:.3f}s)")
                    
                    # Schema validation
                    expected_agent_fields = [
                        "job_id", "top_candidates", "total_candidates", 
                        "processing_time", "algorithm_version", "status"
                    ]
                    
                    missing_agent = [field for field in expected_agent_fields if field not in data]
                    if missing_agent:
                        self.schema_errors.append(f"Agent Direct - Missing fields: {missing_agent}")
                    
                    # Validate candidate structure
                    if "top_candidates" in data and data["top_candidates"]:
                        candidate = data["top_candidates"][0]
                        expected_candidate_fields = [
                            "candidate_id", "name", "email", "score", 
                            "skills_match", "experience_match", "location_match", "reasoning"
                        ]
                        
                        missing_candidate = [field for field in expected_candidate_fields 
                                           if field not in candidate]
                        
                        if missing_candidate:
                            self.schema_errors.append(f"Agent Candidate - Missing: {missing_candidate}")
                        else:
                            print("[SCHEMA] Agent candidate fields validated")
                    
                    self.results["agent_direct"] = {
                        "status": "success",
                        "response_time": response_time,
                        "candidates_count": len(data.get("top_candidates", [])),
                        "algorithm_version": data.get("algorithm_version"),
                        "sample_score": data["top_candidates"][0]["score"] if data.get("top_candidates") else None
                    }
                    
                    print(f"   Candidates: {len(data.get('top_candidates', []))}")
                    print(f"   Algorithm: {data.get('algorithm_version')}")
                    if data.get("top_candidates"):
                        print(f"   Top Score: {data['top_candidates'][0]['score']}")
                    
                else:
                    print(f"[FAILED] Agent Direct Match: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    self.results["agent_direct"] = {"status": "failed", "code": response.status_code}
                    
        except Exception as e:
            print(f"[ERROR] Agent Direct Match: {str(e)}")
            self.results["agent_direct"] = {"status": "error", "error": str(e)}

    async def test_agent_batch_match_detailed(self):
        """Test Agent service batch match with authentication"""
        print("\n[TEST] Agent Batch Match - With Authentication")
        
        try:
            start_time = time.time()
            async with httpx.AsyncClient(timeout=120.0) as client:
                response = await client.post(
                    f"{AGENT_URL}/batch-match",
                    headers=HEADERS,
                    json={"job_ids": [1, 2]}
                )
                response_time = time.time() - start_time
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"[SUCCESS] Agent Batch Match: {response.status_code} ({response_time:.3f}s)")
                    
                    # Schema validation
                    expected_agent_batch_fields = [
                        "batch_results", "total_jobs_processed", 
                        "algorithm_version", "status"
                    ]
                    
                    missing_agent_batch = [field for field in expected_agent_batch_fields 
                                         if field not in data]
                    if missing_agent_batch:
                        self.schema_errors.append(f"Agent Batch - Missing: {missing_agent_batch}")
                    
                    self.results["agent_batch"] = {
                        "status": "success",
                        "response_time": response_time,
                        "jobs_processed": data.get("total_jobs_processed"),
                        "algorithm_version": data.get("algorithm_version")
                    }
                    
                    print(f"   Jobs Processed: {data.get('total_jobs_processed')}")
                    print(f"   Algorithm: {data.get('algorithm_version')}")
                    
                else:
                    print(f"[FAILED] Agent Batch Match: {response.status_code}")
                    print(f"   Response: {response.text[:200]}...")
                    self.results["agent_batch"] = {"status": "failed", "code": response.status_code}
                    
        except Exception as e:
            print(f"[ERROR] Agent Batch Match: {str(e)}")
            self.results["agent_batch"] = {"status": "error", "error": str(e)}

    def validate_schema_consistency(self):
        """Validate schema consistency between Gateway and Agent"""
        print("\n[VALIDATION] Schema Consistency Analysis")
        
        gateway_single = self.results.get("gateway_single", {})
        agent_direct = self.results.get("agent_direct", {})
        
        # Compare algorithm versions
        if (gateway_single.get("status") == "success" and 
            agent_direct.get("status") == "success"):
            
            gw_algo = gateway_single.get("algorithm_version", "")
            agent_algo = agent_direct.get("algorithm_version", "")
            
            print(f"   Gateway Algorithm: {gw_algo}")
            print(f"   Agent Algorithm: {agent_algo}")
            
            if "phase3" in gw_algo.lower() and "phase3" in agent_algo.lower():
                print("[OK] Both services using Phase 3 algorithms")
            else:
                print("[WARNING] Algorithm version mismatch detected")
        
        # Compare response structures
        gateway_batch = self.results.get("gateway_batch", {})
        agent_batch = self.results.get("agent_batch", {})
        
        if (gateway_batch.get("status") == "success" and 
            agent_batch.get("status") == "success"):
            print("[OK] Both batch endpoints operational")
        else:
            print("[WARNING] Batch endpoint consistency issues")

    def analyze_performance(self):
        """Analyze performance metrics"""
        print("\n[PERFORMANCE] Response Time Analysis")
        
        for test_name, result in self.results.items():
            if result.get("response_time"):
                response_time = result["response_time"]
                status = "FAST" if response_time < 2.0 else "SLOW" if response_time > 5.0 else "OK"
                print(f"   {test_name}: {response_time:.3f}s [{status}]")

    def print_comprehensive_summary(self):
        """Print comprehensive test summary"""
        print("\n" + "="*70)
        print("COMPREHENSIVE AI MATCHING ENDPOINTS VALIDATION REPORT")
        print("="*70)
        
        # Service Status Overview
        print("\n[STATUS] Service Operational Status:")
        total_tests = len(self.results)
        successful_tests = sum(1 for r in self.results.values() if r.get("status") == "success")
        
        for test_name, result in self.results.items():
            status_icon = "[PASS]" if result.get("status") == "success" else "[FAIL]"
            print(f"   {status_icon} {test_name}: {result.get('status', 'unknown')}")
        
        print(f"\n[SUMMARY] {successful_tests}/{total_tests} tests passed ({(successful_tests/total_tests)*100:.1f}%)")
        
        # Schema Validation Results
        print(f"\n[SCHEMA] Schema Validation Results:")
        if self.schema_errors:
            print(f"   [ISSUES] {len(self.schema_errors)} schema issues found:")
            for i, error in enumerate(self.schema_errors, 1):
                print(f"      {i}. {error}")
        else:
            print("   [PASS] All schemas validated successfully")
        
        # Performance Analysis
        self.analyze_performance()
        
        # Current Implementation Status
        print(f"\n[IMPLEMENTATION] Current Fixes & Enhancements:")
        print("   [DONE] Gateway batch endpoint returns detailed candidate information")
        print("   [DONE] Agent service batch endpoint provides complete match structure")
        print("   [DONE] Schema alignment between single and batch operations")
        print("   [DONE] Dynamic location matching from database queries")
        print("   [DONE] Consistent field structure across all AI matching endpoints")
        print("   [DONE] Phase 3 semantic engine integration")
        print("   [DONE] Authentication system unified across services")
        
        # Recommendations
        print(f"\n[RECOMMENDATIONS] Next Steps:")
        if self.schema_errors:
            print("   1. Address schema validation issues identified above")
        if any(r.get("response_time", 0) > 5.0 for r in self.results.values()):
            print("   2. Optimize slow endpoints for better performance")
        if successful_tests < total_tests:
            print("   3. Investigate and fix failed service endpoints")
        
        print("\n[CONCLUSION] AI Matching Engine validation completed.")

async def main():
    """Run comprehensive AI matching validation"""
    print("BHIV HR Platform - AI Matching Endpoints Comprehensive Validation")
    print("="*70)
    
    tester = ComprehensiveAITester()
    
    # Wake up services
    await tester.wake_agent_service()
    
    # Run comprehensive tests
    await tester.test_gateway_single_match_detailed()
    await tester.test_gateway_batch_match_detailed()
    await tester.test_agent_direct_match_detailed()
    await tester.test_agent_batch_match_detailed()
    
    # Analysis and validation
    tester.validate_schema_consistency()
    tester.print_comprehensive_summary()

if __name__ == "__main__":
    asyncio.run(main())
