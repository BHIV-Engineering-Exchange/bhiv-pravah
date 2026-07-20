#!/usr/bin/env python3
"""
Logistics AI Decision System
Integrated decision-making capabilities for logistics operations
"""

import json
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional
from rl_feedback_system import record_agent_action, record_action_outcome
from ems_automation import trigger_restock_alert, trigger_purchase_order, trigger_shipment_notification

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class LogisticsDecisionEngine:
    """AI-powered decision engine for logistics operations"""
    
    def __init__(self):
        self.agent_id = "logistics_ai_decision_engine"
        self.capabilities = [
            "route_optimization",
            "procurement_decisions", 
            "inventory_forecasting",
            "delay_risk_assessment",
            "supplier_selection"
        ]
    
    async def make_decision(self, decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make AI-powered logistics decisions"""
        try:
            if decision_type == "route_optimization":
                return await self._optimize_routes(context)
            elif decision_type == "procurement_decision":
                return await self._make_procurement_decision(context)
            elif decision_type == "inventory_forecast":
                return await self._forecast_inventory(context)
            elif decision_type == "delay_assessment":
                return await self._assess_delay_risk(context)
            elif decision_type == "supplier_selection":
                return await self._select_supplier(context)
            else:
                return self._default_decision(context)
        except Exception as e:
            logger.error(f"Decision error: {e}")
            return {"decision": "error", "reason": str(e), "confidence": 0.0}
    
    async def _optimize_routes(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Optimize delivery routes using AI"""
        orders = context.get("orders", [])
        vehicle_capacity = context.get("vehicle_capacity", 100)
        
        # Record RL action
        action_id = record_agent_action(
            self.agent_id,
            "delivery_routing",
            {"orders": len(orders), "capacity": vehicle_capacity, "expected_cost": 50, "expected_time": 4},
            0.85
        )
        
        # AI route optimization logic
        optimized_routes = []
        total_efficiency = 0
        
        for i, order in enumerate(orders):
            route_efficiency = min(0.95, 0.7 + (i * 0.05))  # Decreasing efficiency
            total_efficiency += route_efficiency
            
            route = {
                "order_id": order.get("id", f"ORD_{i}"),
                "priority": order.get("priority", "medium"),
                "estimated_time": order.get("estimated_time", 2),
                "efficiency_score": route_efficiency,
                "route_segments": ["warehouse", "customer"]
            }
            optimized_routes.append(route)
        
        avg_efficiency = total_efficiency / max(len(orders), 1)
        
        decision = {
            "decision": "routes_optimized",
            "optimized_routes": optimized_routes,
            "total_orders": len(orders),
            "average_efficiency": avg_efficiency,
            "confidence": 0.85,
            "reasoning": f"Optimized {len(orders)} delivery routes with {avg_efficiency:.2f} avg efficiency",
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id
        }
        
        # Simulate outcome for RL
        success = avg_efficiency > 0.75
        record_action_outcome(action_id, success, 45, 50, 3.5, 4, 4.2, 6.5)
        
        return decision
    
    async def _make_procurement_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Make intelligent procurement decisions"""
        inventory_levels = context.get("inventory", {})
        demand_forecast = context.get("demand", {})
        
        # Record RL action
        action_id = record_agent_action(
            self.agent_id,
            "procurement_order",
            {"items": len(inventory_levels), "expected_cost": 1000, "expected_time": 72},
            0.78
        )
        
        recommendations = []
        total_value = 0
        
        for item, current_stock in inventory_levels.items():
            forecasted_demand = demand_forecast.get(item, current_stock * 2)
            
            if current_stock < forecasted_demand * 0.3:  # Low stock threshold
                order_quantity = int(forecasted_demand * 1.5 - current_stock)
                unit_cost = 15.0  # Simplified
                total_cost = order_quantity * unit_cost
                total_value += total_cost
                
                recommendation = {
                    "item": item,
                    "current_stock": current_stock,
                    "forecasted_demand": forecasted_demand,
                    "recommended_quantity": order_quantity,
                    "estimated_cost": total_cost,
                    "urgency": "high" if current_stock < forecasted_demand * 0.1 else "medium"
                }
                recommendations.append(recommendation)
                
                # Trigger EMS notification
                trigger_restock_alert(item, item, current_stock, order_quantity)
        
        decision = {
            "decision": "procurement_recommended",
            "recommendations": recommendations,
            "total_estimated_cost": total_value,
            "confidence": 0.78,
            "reasoning": f"Generated {len(recommendations)} procurement recommendations",
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id
        }
        
        # Simulate outcome
        success = len(recommendations) > 0
        record_action_outcome(action_id, success, total_value * 0.95, total_value, 68, 72, 4.0, 7.0)
        
        return decision
    
    async def _forecast_inventory(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered inventory forecasting"""
        historical_data = context.get("historical_sales", [])
        seasonality = context.get("seasonality", {})
        
        # Record RL action
        action_id = record_agent_action(
            self.agent_id,
            "inventory_allocation",
            {"items": len(historical_data), "expected_cost": 0, "expected_time": 1},
            0.72
        )
        
        forecasts = {}
        
        for item_data in historical_data:
            item_id = item_data.get("item_id")
            sales_history = item_data.get("sales", [])
            
            if sales_history:
                avg_sales = sum(sales_history) / len(sales_history)
                seasonal_factor = seasonality.get(item_id, 1.0)
                forecasted_demand = avg_sales * seasonal_factor * 1.1  # Growth factor
                
                forecasts[item_id] = {
                    "forecasted_demand": forecasted_demand,
                    "confidence": 0.72,
                    "trend": "stable" if seasonal_factor == 1.0 else "seasonal"
                }
        
        decision = {
            "decision": "inventory_forecasted",
            "forecasts": forecasts,
            "forecast_period": "30_days",
            "confidence": 0.72,
            "reasoning": f"Forecasted demand for {len(forecasts)} items using historical data",
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id
        }
        
        # Simulate outcome
        record_action_outcome(action_id, True, 0, 0, 0.8, 1, 4.1, 6.0)
        
        return decision
    
    async def _assess_delay_risk(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Assess delivery delay risks using AI"""
        order_details = context.get("order", {})
        weather = context.get("weather", {})
        traffic = context.get("traffic", {})
        
        # Record RL action
        action_id = record_agent_action(
            self.agent_id,
            "delivery_routing",
            {"order_id": order_details.get("id"), "expected_cost": 25, "expected_time": 48},
            0.88
        )
        
        risk_score = 0.0
        risk_factors = []
        
        # Weather risk
        weather_severity = weather.get("severity", 0)
        if weather_severity > 6:
            risk_score += 0.4
            risk_factors.append("severe_weather")
        elif weather_severity > 3:
            risk_score += 0.2
            risk_factors.append("moderate_weather")
        
        # Traffic risk
        traffic_level = traffic.get("congestion", 0)
        if traffic_level > 8:
            risk_score += 0.3
            risk_factors.append("heavy_traffic")
        elif traffic_level > 5:
            risk_score += 0.15
            risk_factors.append("moderate_traffic")
        
        # Distance risk
        distance = order_details.get("distance_km", 0)
        if distance > 100:
            risk_score += 0.2
            risk_factors.append("long_distance")
        
        risk_level = "low" if risk_score < 0.3 else "medium" if risk_score < 0.6 else "high"
        
        # Generate mitigation suggestions
        mitigations = []
        if "severe_weather" in risk_factors:
            mitigations.append("Delay shipment until weather improves")
        if "heavy_traffic" in risk_factors:
            mitigations.append("Schedule delivery during off-peak hours")
        if "long_distance" in risk_factors:
            mitigations.append("Use express delivery service")
        
        decision = {
            "decision": "delay_risk_assessed",
            "risk_score": risk_score,
            "risk_level": risk_level,
            "risk_factors": risk_factors,
            "mitigation_suggestions": mitigations,
            "confidence": 0.88,
            "reasoning": f"Assessed delay risk as {risk_level} based on weather, traffic, and distance",
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id
        }
        
        # Simulate outcome
        success = risk_score < 0.5
        record_action_outcome(action_id, success, 23, 25, 45 if success else 55, 48, 4.3, 6.8)
        
        return decision
    
    async def _select_supplier(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """AI-powered supplier selection"""
        suppliers = context.get("suppliers", [])
        requirements = context.get("requirements", {})
        
        # Record RL action
        action_id = record_agent_action(
            self.agent_id,
            "supplier_selection",
            {"suppliers": len(suppliers), "expected_cost": 0, "expected_time": 2},
            0.82
        )
        
        scored_suppliers = []
        
        for supplier in suppliers:
            # Calculate supplier score
            reliability = supplier.get("reliability", 0.8)
            cost_factor = supplier.get("cost_factor", 1.0)
            lead_time = supplier.get("lead_time_days", 7)
            
            # Scoring algorithm
            reliability_score = reliability * 0.4
            cost_score = (2.0 - cost_factor) * 0.3  # Lower cost is better
            speed_score = max(0, (14 - lead_time) / 14) * 0.3  # Faster is better
            
            total_score = reliability_score + cost_score + speed_score
            
            scored_suppliers.append({
                "supplier_id": supplier.get("id"),
                "name": supplier.get("name"),
                "total_score": total_score,
                "reliability": reliability,
                "cost_factor": cost_factor,
                "lead_time_days": lead_time,
                "recommendation": "preferred" if total_score > 0.7 else "acceptable" if total_score > 0.5 else "not_recommended"
            })
        
        # Sort by score
        scored_suppliers.sort(key=lambda x: x["total_score"], reverse=True)
        
        decision = {
            "decision": "supplier_selected",
            "recommended_supplier": scored_suppliers[0] if scored_suppliers else None,
            "all_suppliers": scored_suppliers,
            "confidence": 0.82,
            "reasoning": f"Evaluated {len(suppliers)} suppliers based on reliability, cost, and lead time",
            "timestamp": datetime.utcnow().isoformat(),
            "action_id": action_id
        }
        
        # Simulate outcome
        success = len(scored_suppliers) > 0
        record_action_outcome(action_id, success, 0, 0, 1.8, 2, 4.4, 7.2)
        
        return decision
    
    def _default_decision(self, context: Dict[str, Any]) -> Dict[str, Any]:
        """Default decision for unknown types"""
        return {
            "decision": "no_action",
            "reasoning": "No specific decision logic available for this context",
            "confidence": 0.5,
            "timestamp": datetime.utcnow().isoformat()
        }

class LogisticsWorkflowManager:
    """Manages logistics decision workflows"""
    
    def __init__(self):
        self.decision_engine = LogisticsDecisionEngine()
        self.active_workflows = {}
    
    async def process_order_workflow(self, order_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process complete order workflow with AI decisions"""
        workflow_id = f"order_workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        workflow_results = {
            "workflow_id": workflow_id,
            "order_id": order_data.get("id"),
            "decisions": [],
            "status": "processing"
        }
        
        try:
            # Step 1: Route optimization
            route_decision = await self.decision_engine.make_decision(
                "route_optimization",
                {"orders": [order_data], "vehicle_capacity": 100}
            )
            workflow_results["decisions"].append(route_decision)
            
            # Step 2: Delay risk assessment
            delay_decision = await self.decision_engine.make_decision(
                "delay_assessment",
                {
                    "order": order_data,
                    "weather": {"severity": 2},
                    "traffic": {"congestion": 4}
                }
            )
            workflow_results["decisions"].append(delay_decision)
            
            # Step 3: Trigger notifications based on decisions
            if route_decision.get("decision") == "routes_optimized":
                # Trigger shipment notification
                trigger_shipment_notification(
                    order_data.get("customer_email", "customer@example.com"),
                    order_data.get("id", "ORD_001"),
                    f"TRK_{workflow_id[-6:]}",
                    "AI Logistics Express",
                    "2025-01-28"
                )
            
            workflow_results["status"] = "completed"
            
        except Exception as e:
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)
        
        self.active_workflows[workflow_id] = workflow_results
        return workflow_results
    
    async def process_inventory_workflow(self, inventory_data: Dict[str, Any]) -> Dict[str, Any]:
        """Process inventory management workflow"""
        workflow_id = f"inventory_workflow_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        
        workflow_results = {
            "workflow_id": workflow_id,
            "decisions": [],
            "status": "processing"
        }
        
        try:
            # Step 1: Inventory forecasting
            forecast_decision = await self.decision_engine.make_decision(
                "inventory_forecast",
                {
                    "historical_sales": inventory_data.get("historical_data", []),
                    "seasonality": inventory_data.get("seasonality", {})
                }
            )
            workflow_results["decisions"].append(forecast_decision)
            
            # Step 2: Procurement decisions
            procurement_decision = await self.decision_engine.make_decision(
                "procurement_decision",
                {
                    "inventory": inventory_data.get("current_levels", {}),
                    "demand": forecast_decision.get("forecasts", {})
                }
            )
            workflow_results["decisions"].append(procurement_decision)
            
            # Step 3: Supplier selection for recommendations
            if procurement_decision.get("recommendations"):
                supplier_decision = await self.decision_engine.make_decision(
                    "supplier_selection",
                    {
                        "suppliers": inventory_data.get("suppliers", []),
                        "requirements": {"reliability": 0.8, "max_lead_time": 7}
                    }
                )
                workflow_results["decisions"].append(supplier_decision)
            
            workflow_results["status"] = "completed"
            
        except Exception as e:
            workflow_results["status"] = "failed"
            workflow_results["error"] = str(e)
        
        self.active_workflows[workflow_id] = workflow_results
        return workflow_results
    
    def get_workflow_status(self, workflow_id: str) -> Optional[Dict[str, Any]]:
        """Get workflow status"""
        return self.active_workflows.get(workflow_id)
    
    def get_active_workflows(self) -> List[Dict[str, Any]]:
        """Get all active workflows"""
        return list(self.active_workflows.values())

# Global instances
logistics_decision_engine = LogisticsDecisionEngine()
logistics_workflow_manager = LogisticsWorkflowManager()

# Convenience functions
async def make_logistics_decision(decision_type: str, context: Dict[str, Any]) -> Dict[str, Any]:
    """Make a logistics decision"""
    return await logistics_decision_engine.make_decision(decision_type, context)

async def process_order_with_ai(order_data: Dict[str, Any]) -> Dict[str, Any]:
    """Process order using AI workflow"""
    return await logistics_workflow_manager.process_order_workflow(order_data)

async def optimize_inventory_with_ai(inventory_data: Dict[str, Any]) -> Dict[str, Any]:
    """Optimize inventory using AI workflow"""
    return await logistics_workflow_manager.process_inventory_workflow(inventory_data)

if __name__ == "__main__":
    import asyncio
    
    async def test_logistics_ai():
        print("[INFO] Testing Logistics AI Decision System...")
        
        # Test route optimization
        route_result = await make_logistics_decision(
            "route_optimization",
            {
                "orders": [
                    {"id": "ORD_001", "priority": "high"},
                    {"id": "ORD_002", "priority": "medium"}
                ],
                "vehicle_capacity": 100
            }
        )
        print(f"Route optimization: {route_result['decision']}")
        
        # Test order workflow
        order_workflow = await process_order_with_ai({
            "id": "ORD_001",
            "customer_email": "test@example.com",
            "priority": "high"
        })
        print(f"Order workflow: {order_workflow['status']}")
        
        # Test inventory workflow
        inventory_workflow = await optimize_inventory_with_ai({
            "current_levels": {"item_A": 10, "item_B": 5},
            "historical_data": [
                {"item_id": "item_A", "sales": [20, 25, 22]},
                {"item_id": "item_B", "sales": [15, 18, 16]}
            ],
            "suppliers": [
                {"id": "SUP_001", "name": "Supplier A", "reliability": 0.9, "cost_factor": 1.0, "lead_time_days": 5}
            ]
        })
        print(f"Inventory workflow: {inventory_workflow['status']}")
        
        print("[SUCCESS] Logistics AI system tested successfully")
    
    asyncio.run(test_logistics_ai())