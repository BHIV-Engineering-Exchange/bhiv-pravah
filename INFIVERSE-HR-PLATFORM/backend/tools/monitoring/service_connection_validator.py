#!/usr/bin/env python3
"""
🔍 BHIV HR Platform - Service Connection & Routing Validator
Comprehensive validation of all service connections and routing configurations
"""

import asyncio
import httpx
import json
import os
import sys
import time
from datetime import datetime, timezone
from typing import Dict, List, Any, Optional
import logging
from urllib.parse import urljoin, urlparse

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

class ServiceConnectionValidator:
    def __init__(self):
        """Initialize the service connection validator"""
        
        # Service configurations
        self.services = {
            "gateway": {
                "local": "http://localhost:8000",
                "production": "https://bhiv-hr-gateway-ltg0.onrender.com",
                "health_endpoint": "/health",
                "test_endpoints": ["/", "/docs", "/v1/jobs", "/v1/candidates"],
                "expected_status": [200, 401]  # 401 for protected endpoints without auth
            },
            "agent": {
                "local": "http://localhost:9000",
                "production": "https://bhiv-hr-agent-nhgg.onrender.com",
                "health_endpoint": "/health",
                "test_endpoints": ["/", "/test-db", "/match"],
                "expected_status": [200, 401, 422]
            },
            "langgraph": {
                "local": "http://localhost:9001",
                "production": "https://bhiv-hr-langgraph.onrender.com",
                "health_endpoint": "/health",
                "test_endpoints": ["/", "/workflows", "/workflows/stats"],
                "expected_status": [200, 401]
            },
            "hr_portal": {
                "local": "http://localhost:8501",
                "production": "https://bhiv-hr-portal-u670.onrender.com",
                "health_endpoint": "/health",
                "test_endpoints": ["/"],
                "expected_status": [200, 404]
            },
            "client_portal": {
                "local": "http://localhost:8502",
                "production": "https://bhiv-hr-client-portal-3iod.onrender.com",
                "health_endpoint": "/health",
                "test_endpoints": ["/"],
                "expected_status": [200, 404]
            },
            "candidate_portal": {
                "local": "http://localhost:8503",
                "production": "https://bhiv-hr-candidate-portal-abe6.onrender.com",
                "health_endpoint": "/health",
                "test_endpoints": ["/"],
                "expected_status": [200, 404]
            }
        }
        
        # Environment detection
        self.environment = self._detect_environment()
        
        # API key for authenticated requests
        self.api_key = os.getenv("API_KEY_SECRET")
        
        # Results storage
        self.results = {
            "environment": self.environment,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "services": {},
            "routing_tests": {},
            "integration_tests": {},
            "summary": {
                "total_services": len(self.services),
                "healthy_services": 0,
                "failed_services": 0,
                "total_endpoints": 0,
                "working_endpoints": 0,
                "failed_endpoints": 0
            }
        }

    def _detect_environment(self) -> str:
        """Detect current environment (local/production)"""
        if os.getenv("RENDER"):
            return "production"
        elif os.getenv("DOCKER_ENV"):
            return "docker"
        else:
            return "local"

    async def validate_service_connection(self, service_name: str, service_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate connection to a specific service"""
        logger.info(f"🔍 Validating {service_name} service connection...")
        
        # Get service URL based on environment
        service_url = service_config.get(self.environment, service_config.get("local"))
        
        result = {
            "service": service_name,
            "url": service_url,
            "environment": self.environment,
            "status": "unknown",
            "health_check": {},
            "endpoint_tests": [],
            "response_times": [],
            "errors": []
        }
        
        try:
            # Test health endpoint
            health_result = await self._test_endpoint(
                service_url, 
                service_config["health_endpoint"],
                expected_status=service_config["expected_status"]
            )
            
            result["health_check"] = health_result
            
            if health_result["success"]:
                result["status"] = "healthy"
                self.results["summary"]["healthy_services"] += 1
                logger.info(f"✅ {service_name} health check passed")
            else:
                result["status"] = "unhealthy"
                self.results["summary"]["failed_services"] += 1
                logger.warning(f"⚠️ {service_name} health check failed")
            
            # Test additional endpoints
            for endpoint in service_config["test_endpoints"]:
                endpoint_result = await self._test_endpoint(
                    service_url,
                    endpoint,
                    expected_status=service_config["expected_status"]
                )
                
                result["endpoint_tests"].append(endpoint_result)
                result["response_times"].append(endpoint_result.get("response_time", 0))
                
                self.results["summary"]["total_endpoints"] += 1
                
                if endpoint_result["success"]:
                    self.results["summary"]["working_endpoints"] += 1
                else:
                    self.results["summary"]["failed_endpoints"] += 1
                    result["errors"].append(f"Endpoint {endpoint}: {endpoint_result.get('error', 'Unknown error')}")
            
            # Calculate average response time
            if result["response_times"]:
                result["avg_response_time"] = sum(result["response_times"]) / len(result["response_times"])
            else:
                result["avg_response_time"] = 0
                
        except Exception as e:
            result["status"] = "error"
            result["errors"].append(f"Connection validation failed: {str(e)}")
            self.results["summary"]["failed_services"] += 1
            logger.error(f"❌ {service_name} validation failed: {e}")
        
        return result

    async def _test_endpoint(self, base_url: str, endpoint: str, expected_status: List[int] = None) -> Dict[str, Any]:
        """Test a specific endpoint"""
        if expected_status is None:
            expected_status = [200]
        
        url = urljoin(base_url, endpoint)
        start_time = time.time()
        
        result = {
            "endpoint": endpoint,
            "url": url,
            "success": False,
            "status_code": 0,
            "response_time": 0,
            "error": None,
            "response_size": 0
        }
        
        try:
            headers = {}
            
            # Add authentication for protected endpoints
            if self.api_key and ("/v1/" in endpoint or endpoint in ["/match", "/workflows"]):
                headers["Authorization"] = f"Bearer {self.api_key}"
            
            async with httpx.AsyncClient(timeout=30) as client:
                response = await client.get(url, headers=headers)
                
                result["status_code"] = response.status_code
                result["response_time"] = time.time() - start_time
                result["response_size"] = len(response.content)
                
                # Check if status code is expected
                if response.status_code in expected_status:
                    result["success"] = True
                else:
                    result["error"] = f"Unexpected status code: {response.status_code}"
                
        except httpx.TimeoutException:
            result["error"] = "Request timeout"
            result["response_time"] = time.time() - start_time
        except httpx.ConnectError:
            result["error"] = "Connection failed"
            result["response_time"] = time.time() - start_time
        except Exception as e:
            result["error"] = f"Request failed: {str(e)}"
            result["response_time"] = time.time() - start_time
        
        return result

    async def test_service_routing(self) -> Dict[str, Any]:
        """Test routing between services"""
        logger.info("🔄 Testing service routing and integration...")
        
        routing_results = {
            "gateway_to_agent": {},
            "gateway_to_langgraph": {},
            "cross_service_communication": {},
            "routing_errors": []
        }
        
        try:
            # Test Gateway to Agent routing
            if self.results["services"].get("gateway", {}).get("status") == "healthy" and \
               self.results["services"].get("agent", {}).get("status") == "healthy":
                
                gateway_url = self.results["services"]["gateway"]["url"]
                
                # Test AI matching endpoint (routes to agent)
                routing_test = await self._test_endpoint(
                    gateway_url,
                    "/v1/match/1/top",
                    expected_status=[200, 401, 404, 422]
                )
                
                routing_results["gateway_to_agent"] = routing_test
                
                if routing_test["success"]:
                    logger.info("✅ Gateway to Agent routing working")
                else:
                    logger.warning("⚠️ Gateway to Agent routing issues detected")
                    routing_results["routing_errors"].append("Gateway to Agent routing failed")
            
            # Test Gateway to LangGraph routing
            if self.results["services"].get("gateway", {}).get("status") == "healthy" and \
               self.results["services"].get("langgraph", {}).get("status") == "healthy":
                
                gateway_url = self.results["services"]["gateway"]["url"]
                
                # Test workflow endpoint (may route to langgraph)
                routing_test = await self._test_endpoint(
                    gateway_url,
                    "/api/v1/workflows",
                    expected_status=[200, 401, 404, 405]
                )
                
                routing_results["gateway_to_langgraph"] = routing_test
                
                if routing_test["success"]:
                    logger.info("✅ Gateway to LangGraph routing working")
                else:
                    logger.info("ℹ️ Gateway to LangGraph routing not configured (expected)")
            
        except Exception as e:
            routing_results["routing_errors"].append(f"Routing test failed: {str(e)}")
            logger.error(f"❌ Routing test failed: {e}")
        
        return routing_results

    async def test_database_connections(self) -> Dict[str, Any]:
        """Test database connectivity through services"""
        logger.info("🗄️ Testing database connections...")
        
        db_results = {
            "gateway_db": {},
            "agent_db": {},
            "database_errors": []
        }
        
        try:
            # Test Gateway database connection
            if self.results["services"].get("gateway", {}).get("status") == "healthy":
                gateway_url = self.results["services"]["gateway"]["url"]
                
                db_test = await self._test_endpoint(
                    gateway_url,
                    "/v1/test-candidates",
                    expected_status=[200, 401]
                )
                
                db_results["gateway_db"] = db_test
                
                if db_test["success"]:
                    logger.info("✅ Gateway database connection working")
                else:
                    logger.warning("⚠️ Gateway database connection issues")
                    db_results["database_errors"].append("Gateway database connection failed")
            
            # Test Agent database connection
            if self.results["services"].get("agent", {}).get("status") == "healthy":
                agent_service_url = self.results["services"]["agent"]["url"]
                
                db_test = await self._test_endpoint(
                    agent_service_url,
                    "/test-db",
                    expected_status=[200, 401]
                )
                
                db_results["agent_db"] = db_test
                
                if db_test["success"]:
                    logger.info("✅ Agent database connection working")
                else:
                    logger.warning("⚠️ Agent database connection issues")
                    db_results["database_errors"].append("Agent database connection failed")
                    
        except Exception as e:
            db_results["database_errors"].append(f"Database test failed: {str(e)}")
            logger.error(f"❌ Database test failed: {e}")
        
        return db_results

    async def validate_all_connections(self) -> Dict[str, Any]:
        """Run comprehensive validation of all service connections"""
        logger.info("🚀 Starting comprehensive service connection validation...")
        
        # Validate each service
        for service_name, service_config in self.services.items():
            service_result = await self.validate_service_connection(service_name, service_config)
            self.results["services"][service_name] = service_result
        
        # Test routing between services
        self.results["routing_tests"] = await self.test_service_routing()
        
        # Test database connections
        self.results["integration_tests"]["database"] = await self.test_database_connections()
        
        # Generate summary
        self.results["summary"]["success_rate"] = (
            self.results["summary"]["working_endpoints"] / 
            max(self.results["summary"]["total_endpoints"], 1) * 100
        )
        
        logger.info("✅ Comprehensive validation completed")
        return self.results

    def generate_report(self) -> str:
        """Generate comprehensive validation report"""
        report_parts = []
        
        # Header
        report_parts.extend([
            f"\n{'='*80}\n",
            f"🔍 BHIV HR Platform - Service Connection Validation Report\n",
            f"{'='*80}\n\n",
            f"Environment: {self.results['environment']}\n",
            f"Timestamp: {self.results['timestamp']}\n\n"
        ])
        
        # Summary
        summary = self.results["summary"]
        report_parts.extend([
            f"📊 SUMMARY\n",
            f"Total Services: {summary['total_services']}\n",
            f"Healthy Services: {summary['healthy_services']} ✅\n",
            f"Failed Services: {summary['failed_services']} ❌\n",
            f"Total Endpoints: {summary['total_endpoints']}\n",
            f"Working Endpoints: {summary['working_endpoints']} ✅\n",
            f"Failed Endpoints: {summary['failed_endpoints']} ❌\n",
            f"Success Rate: {summary.get('success_rate', 0):.1f}%\n\n"
        ])
        
        # Service Details
        report_parts.append("🔍 SERVICE DETAILS\n")
        for service_name, service_result in self.results["services"].items():
            status_icon = "✅" if service_result["status"] == "healthy" else "❌"
            report_parts.extend([
                f"  {service_name}: {service_result['status']} {status_icon}\n",
                f"    URL: {service_result['url']}\n",
                f"    Avg Response Time: {service_result.get('avg_response_time', 0):.3f}s\n"
            ])
            
            if service_result.get("errors"):
                report_parts.append(f"    Errors: {len(service_result['errors'])}\n")
                for error in service_result["errors"][:3]:  # Show first 3 errors
                    report_parts.append(f"      - {error}\n")
            
            report_parts.append("\n")
        
        # Routing Tests
        if self.results.get("routing_tests"):
            report_parts.append("🔄 ROUTING TESTS\n")
            routing = self.results["routing_tests"]
            
            if routing.get("gateway_to_agent"):
                status = "✅" if routing["gateway_to_agent"]["success"] else "❌"
                report_parts.append(f"  Gateway → Agent: {status}\n")
            
            if routing.get("gateway_to_langgraph"):
                status = "✅" if routing["gateway_to_langgraph"]["success"] else "❌"
                report_parts.append(f"  Gateway → LangGraph: {status}\n")
            
            if routing.get("routing_errors"):
                report_parts.append(f"  Routing Errors: {len(routing['routing_errors'])}\n")
            
            report_parts.append("\n")
        
        # Database Tests
        if self.results.get("integration_tests", {}).get("database"):
            report_parts.append("🗄️ DATABASE TESTS\n")
            db_tests = self.results["integration_tests"]["database"]
            
            if db_tests.get("gateway_db"):
                status = "✅" if db_tests["gateway_db"]["success"] else "❌"
                report_parts.append(f"  Gateway DB: {status}\n")
            
            if db_tests.get("agent_db"):
                status = "✅" if db_tests["agent_db"]["success"] else "❌"
                report_parts.append(f"  Agent DB: {status}\n")
            
            if db_tests.get("database_errors"):
                report_parts.append(f"  DB Errors: {len(db_tests['database_errors'])}\n")
            
            report_parts.append("\n")
        
        # Recommendations
        report_parts.append("💡 RECOMMENDATIONS\n")
        
        if summary["failed_services"] > 0:
            report_parts.append("  - Review failed services and check deployment status\n")
        
        if summary["failed_endpoints"] > 0:
            report_parts.append("  - Investigate failed endpoints for routing or authentication issues\n")
        
        if self.results.get("routing_tests", {}).get("routing_errors"):
            report_parts.append("  - Fix service routing configurations\n")
        
        if summary["success_rate"] < 90:
            report_parts.append("  - System requires immediate attention - success rate below 90%\n")
        elif summary["success_rate"] < 95:
            report_parts.append("  - Consider investigating failed endpoints for optimization\n")
        else:
            report_parts.append("  - System is performing well - maintain current configuration\n")
        
        report_parts.append(f"\n{'='*80}\n")
        
        return ''.join(report_parts)

    async def save_results(self, filename: str = None):
        """Save validation results to file"""
        if filename is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"service_validation_{timestamp}.json"
        
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, indent=2, default=str)
            
            logger.info(f"📄 Results saved to {filename}")
        except Exception as e:
            logger.error(f"❌ Failed to save results: {e}")

async def main():
    """Main function to run service connection validation"""
    validator = ServiceConnectionValidator()
    
    try:
        # Run comprehensive validation
        results = await validator.validate_all_connections()
        
        # Generate and display report
        report = validator.generate_report()
        print(report)
        
        # Save results
        await validator.save_results()
        
        # Save report
        with open("service_validation_report.txt", "w", encoding="utf-8") as f:
            f.write(report)
        
        logger.info("📄 Report saved to service_validation_report.txt")
        
        # Return exit code based on results
        if results["summary"]["failed_services"] == 0:
            return 0
        else:
            return 1
            
    except Exception as e:
        logger.error(f"❌ Validation failed: {e}")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)