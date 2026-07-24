"""
Vehicle Maintenance Agent
Analyzes vehicle maintenance needs and schedules upcoming services
"""

import json
from datetime import datetime, timedelta
from typing import Dict, Any, List
from agents.base_agent import BaseAgent
from utils.logger import get_logger

logger = get_logger(__name__)

class VehicleMaintenanceAgent(BaseAgent):
    def __init__(self):
        super().__init__("vehicle_maintenance")
        
        # Standard maintenance intervals (miles)
        self.maintenance_intervals = {
            "oil_change": {
                "interval_miles": 5000,
                "interval_months": 6,
                "cost": 75.0,
                "priority": "medium"
            },
            "tire_rotation": {
                "interval_miles": 7500,
                "interval_months": 6,
                "cost": 50.0,
                "priority": "low"
            },
            "air_filter": {
                "interval_miles": 15000,
                "interval_months": 12,
                "cost": 25.0,
                "priority": "low"
            },
            "brake_inspection": {
                "interval_miles": 20000,
                "interval_months": 24,
                "cost": 100.0,
                "priority": "high"
            },
            "transmission_service": {
                "interval_miles": 30000,
                "interval_months": 36,
                "cost": 200.0,
                "priority": "medium"
            },
            "coolant_flush": {
                "interval_miles": 30000,
                "interval_months": 36,
                "cost": 150.0,
                "priority": "medium"
            },
            "spark_plugs": {
                "interval_miles": 30000,
                "interval_months": 36,
                "cost": 120.0,
                "priority": "medium"
            },
            "timing_belt": {
                "interval_miles": 60000,
                "interval_months": 72,
                "cost": 800.0,
                "priority": "high"
            }
        }
    
    def process(self, input_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process vehicle maintenance data and return maintenance schedule
        """
        try:
            vehicle_info = input_data.get("vehicle_info", {})
            make = vehicle_info.get("make")
            model = vehicle_info.get("model")
            year = vehicle_info.get("year")
            current_mileage = vehicle_info.get("mileage", 0)
            last_service_date = vehicle_info.get("last_service_date")
            service_history = vehicle_info.get("service_history", [])
            
            logger.info(f"Analyzing maintenance for: {year} {make} {model} at {current_mileage} miles")
            
            # Parse service history
            service_records = self._parse_service_history(service_history)
            
            # Calculate upcoming services
            upcoming_services = self._calculate_upcoming_services(
                current_mileage, service_records, last_service_date
            )
            
            # Calculate overdue services
            overdue_services = self._calculate_overdue_services(
                current_mileage, service_records, last_service_date
            )
            
            # Calculate total estimated cost
            total_cost = sum(service["estimated_cost"] for service in upcoming_services)
            total_cost += sum(service["estimated_cost"] for service in overdue_services)
            
            maintenance_schedule = {
                "upcoming_services": upcoming_services,
                "overdue_services": overdue_services,
                "total_estimated_cost": round(total_cost, 2)
            }
            
            result = {
                "maintenance_schedule": maintenance_schedule,
                "vehicle_info": {
                    "make": make,
                    "model": model,
                    "year": year,
                    "current_mileage": current_mileage
                },
                "services_analyzed": len(self.maintenance_intervals),
                "status": "completed"
            }
            
            logger.info(f"Maintenance analysis completed: {len(upcoming_services)} upcoming, {len(overdue_services)} overdue")
            return result
            
        except Exception as e:
            logger.error(f"Error in vehicle maintenance processing: {e}")
            return {
                "error": f"Vehicle maintenance analysis failed: {str(e)}",
                "status": "failed"
            }
    
    def _parse_service_history(self, service_history: List[Dict]) -> Dict[str, Dict]:
        """Parse service history into a lookup dictionary"""
        service_records = {}
        
        for service in service_history:
            service_type = service.get("service_type")
            service_date = service.get("date")
            service_mileage = service.get("mileage", 0)
            
            if service_type:
                service_records[service_type] = {
                    "date": service_date,
                    "mileage": service_mileage
                }
        
        return service_records
    
    def _calculate_upcoming_services(self, current_mileage: int, service_records: Dict, last_service_date: str) -> List[Dict]:
        """Calculate upcoming maintenance services"""
        upcoming_services = []
        current_date = datetime.now()
        
        for service_type, interval_info in self.maintenance_intervals.items():
            interval_miles = interval_info["interval_miles"]
            interval_months = interval_info["interval_months"]
            cost = interval_info["cost"]
            priority = interval_info["priority"]
            
            # Get last service info
            last_service = service_records.get(service_type)
            
            if last_service:
                last_service_mileage = last_service["mileage"]
                last_service_date_str = last_service["date"]
            else:
                # If no service record, assume it was done at 0 miles
                last_service_mileage = 0
                last_service_date_str = None
            
            # Calculate due mileage
            due_mileage = last_service_mileage + interval_miles
            
            # Calculate due date
            if last_service_date_str:
                try:
                    last_date = datetime.strptime(last_service_date_str, "%Y-%m-%d")
                    due_date = last_date + timedelta(days=interval_months * 30)
                except:
                    due_date = current_date + timedelta(days=interval_months * 30)
            else:
                due_date = current_date + timedelta(days=interval_months * 30)
            
            # Check if service is upcoming (within next 5000 miles or 6 months)
            miles_until_due = due_mileage - current_mileage
            days_until_due = (due_date - current_date).days
            
            if 0 < miles_until_due <= 5000 or 0 < days_until_due <= 180:
                upcoming_services.append({
                    "service_type": service_type,
                    "due_mileage": due_mileage,
                    "due_date": due_date.strftime("%Y-%m-%d"),
                    "priority": priority,
                    "estimated_cost": cost,
                    "miles_until_due": miles_until_due,
                    "days_until_due": days_until_due
                })
        
        # Sort by priority and due date
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        upcoming_services.sort(key=lambda x: (priority_order.get(x["priority"], 4), x["days_until_due"]))
        
        return upcoming_services
    
    def _calculate_overdue_services(self, current_mileage: int, service_records: Dict, last_service_date: str) -> List[Dict]:
        """Calculate overdue maintenance services"""
        overdue_services = []
        current_date = datetime.now()
        
        for service_type, interval_info in self.maintenance_intervals.items():
            interval_miles = interval_info["interval_miles"]
            interval_months = interval_info["interval_months"]
            cost = interval_info["cost"]
            priority = interval_info["priority"]
            
            # Get last service info
            last_service = service_records.get(service_type)
            
            if last_service:
                last_service_mileage = last_service["mileage"]
                last_service_date_str = last_service["date"]
            else:
                # If no service record, assume it was done at 0 miles
                last_service_mileage = 0
                last_service_date_str = None
            
            # Calculate due mileage and date
            due_mileage = last_service_mileage + interval_miles
            
            if last_service_date_str:
                try:
                    last_date = datetime.strptime(last_service_date_str, "%Y-%m-%d")
                    due_date = last_date + timedelta(days=interval_months * 30)
                except:
                    due_date = current_date - timedelta(days=interval_months * 30)
            else:
                due_date = current_date - timedelta(days=interval_months * 30)
            
            # Check if service is overdue
            miles_overdue = current_mileage - due_mileage
            days_overdue = (current_date - due_date).days
            
            if miles_overdue > 0 or days_overdue > 0:
                # Increase priority for overdue services
                overdue_priority = priority
                if days_overdue > 180 or miles_overdue > 10000:
                    overdue_priority = "urgent"
                elif days_overdue > 90 or miles_overdue > 5000:
                    if priority in ["low", "medium"]:
                        overdue_priority = "high"
                
                overdue_services.append({
                    "service_type": service_type,
                    "overdue_by_miles": max(0, miles_overdue),
                    "overdue_by_days": max(0, days_overdue),
                    "priority": overdue_priority,
                    "estimated_cost": cost,
                    "due_mileage": due_mileage,
                    "due_date": due_date.strftime("%Y-%m-%d")
                })
        
        # Sort by priority and overdue amount
        priority_order = {"urgent": 0, "high": 1, "medium": 2, "low": 3}
        overdue_services.sort(key=lambda x: (priority_order.get(x["priority"], 4), -x["overdue_by_days"]))
        
        return overdue_services

def run(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """Entry point for the agent"""
    agent = VehicleMaintenanceAgent()
    return agent.process(input_data)
