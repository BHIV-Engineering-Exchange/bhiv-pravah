"""
Auto Diagnostics Agent
Analyzes vehicle diagnostic data and provides repair recommendations
"""

import json
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger(__name__)

class AutoDiagnosticsAgent(BaseAgent):
    def __init__(self):
        super().__init__("auto_diagnostics")
        
        # OBD-II error code database (simplified)
        self.error_codes = {
            "P0301": {
                "description": "Cylinder 1 misfire",
                "severity": "medium",
                "recommendations": ["Replace spark plug cylinder 1", "Check ignition coil", "Inspect fuel injector"],
                "estimated_cost": 150.0
            },
            "P0302": {
                "description": "Cylinder 2 misfire",
                "severity": "medium", 
                "recommendations": ["Replace spark plug cylinder 2", "Check ignition coil", "Inspect fuel injector"],
                "estimated_cost": 150.0
            },
            "P0420": {
                "description": "Catalytic converter efficiency below threshold",
                "severity": "medium",
                "recommendations": ["Inspect catalytic converter", "Check oxygen sensors", "Replace catalytic converter if needed"],
                "estimated_cost": 800.0
            },
            "P0171": {
                "description": "System too lean (Bank 1)",
                "severity": "medium",
                "recommendations": ["Check for vacuum leaks", "Clean mass airflow sensor", "Replace air filter"],
                "estimated_cost": 200.0
            },
            "P0128": {
                "description": "Coolant thermostat malfunction",
                "severity": "low",
                "recommendations": ["Replace thermostat", "Check coolant level", "Inspect cooling system"],
                "estimated_cost": 250.0
            },
            "P0442": {
                "description": "Evaporative emission control system leak detected (small leak)",
                "severity": "low",
                "recommendations": ["Check gas cap", "Inspect EVAP system", "Replace gas cap if needed"],
                "estimated_cost": 100.0
            }
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process vehicle diagnostic data and return diagnosis
        """
        try:
            vehicle_data = input_data.get("vehicle_data", {})
            vin = vehicle_data.get("vin")
            make = vehicle_data.get("make")
            model = vehicle_data.get("model")
            year = vehicle_data.get("year")
            mileage = vehicle_data.get("mileage", 0)
            error_codes = vehicle_data.get("error_codes", [])
            symptoms = vehicle_data.get("symptoms", [])
            
            logger.info(f"Diagnosing vehicle: {year} {make} {model} (VIN: {vin})")
            
            issues = []
            recommendations = []
            total_cost = 0.0
            max_severity = "low"
            
            # Process error codes
            for code in error_codes:
                if code in self.error_codes:
                    error_info = self.error_codes[code]
                    issues.append(error_info["description"])
                    recommendations.extend(error_info["recommendations"])
                    total_cost += error_info["estimated_cost"]
                    
                    # Update severity (prioritize higher severity)
                    if error_info["severity"] == "critical":
                        max_severity = "critical"
                    elif error_info["severity"] == "high" and max_severity != "critical":
                        max_severity = "high"
                    elif error_info["severity"] == "medium" and max_severity not in ["critical", "high"]:
                        max_severity = "medium"
                else:
                    # Unknown error code
                    issues.append(f"Unknown error code: {code}")
                    recommendations.append(f"Consult service manual for error code {code}")
                    total_cost += 100.0  # Default diagnostic cost
            
            # Process symptoms (basic symptom analysis)
            symptom_analysis = self._analyze_symptoms(symptoms)
            if symptom_analysis:
                issues.extend(symptom_analysis["issues"])
                recommendations.extend(symptom_analysis["recommendations"])
                total_cost += symptom_analysis["cost"]
                
                # Update severity if symptom analysis indicates higher severity
                if symptom_analysis["severity"] == "critical":
                    max_severity = "critical"
                elif symptom_analysis["severity"] == "high" and max_severity != "critical":
                    max_severity = "high"
            
            # If no issues found
            if not issues:
                issues.append("No diagnostic issues detected")
                recommendations.append("Vehicle appears to be in good condition")
                max_severity = "low"
                total_cost = 0.0
            
            # Remove duplicate recommendations
            recommendations = list(set(recommendations))
            
            diagnosis = {
                "issues": issues,
                "severity": max_severity,
                "recommendations": recommendations,
                "estimated_cost": round(total_cost, 2)
            }
            
            result = {
                "diagnosis": diagnosis,
                "vehicle_info": {
                    "vin": vin,
                    "make": make,
                    "model": model,
                    "year": year,
                    "mileage": mileage
                },
                "codes_analyzed": len(error_codes),
                "symptoms_analyzed": len(symptoms),
                "status": "completed"
            }
            
            logger.info(f"Diagnosis completed: {len(issues)} issues found, severity: {max_severity}")
            return result
            
        except Exception as e:
            logger.error(f"Error in auto diagnostics processing: {e}")
            return {
                "error": f"Auto diagnostics failed: {str(e)}",
                "status": "failed"
            }
    
    def _analyze_symptoms(self, symptoms: List[str]) -> Dict[str, Any]:
        """Analyze reported symptoms"""
        if not symptoms:
            return None
        
        issues = []
        recommendations = []
        cost = 0.0
        severity = "low"
        
        symptom_keywords = {
            "misfire": {
                "issues": ["Engine misfire detected"],
                "recommendations": ["Check spark plugs", "Inspect ignition system"],
                "cost": 200.0,
                "severity": "medium"
            },
            "rough idle": {
                "issues": ["Rough idle condition"],
                "recommendations": ["Clean throttle body", "Check idle air control valve"],
                "cost": 150.0,
                "severity": "low"
            },
            "stalling": {
                "issues": ["Engine stalling"],
                "recommendations": ["Check fuel system", "Inspect ignition system", "Diagnose engine sensors"],
                "cost": 300.0,
                "severity": "high"
            },
            "overheating": {
                "issues": ["Engine overheating"],
                "recommendations": ["Check coolant level", "Inspect radiator", "Check water pump"],
                "cost": 400.0,
                "severity": "critical"
            },
            "poor fuel economy": {
                "issues": ["Poor fuel economy"],
                "recommendations": ["Check air filter", "Inspect fuel injectors", "Check tire pressure"],
                "cost": 100.0,
                "severity": "low"
            }
        }
        
        for symptom in symptoms:
            symptom_lower = symptom.lower()
            for keyword, info in symptom_keywords.items():
                if keyword in symptom_lower:
                    issues.extend(info["issues"])
                    recommendations.extend(info["recommendations"])
                    cost += info["cost"]
                    
                    # Update severity
                    if info["severity"] == "critical":
                        severity = "critical"
                    elif info["severity"] == "high" and severity != "critical":
                        severity = "high"
                    elif info["severity"] == "medium" and severity not in ["critical", "high"]:
                        severity = "medium"
        
        if issues:
            return {
                "issues": list(set(issues)),
                "recommendations": list(set(recommendations)),
                "cost": cost,
                "severity": severity
            }
        
        return None

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the agent"""
    agent = AutoDiagnosticsAgent()
    return agent.process(input_data)

async def process(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Async wrapper for compatibility"""
    return run(input_data)
