#!/usr/bin/env python3
"""
RL-Integrated AI Agents
Enhanced agents with Noopur's Rishabh RL feedback integration
"""

import time
import random
from datetime import datetime, timedelta
from typing import Dict, List, Tuple
from database.service import DatabaseService
from ems_automation import trigger_restock_alert, trigger_purchase_order, trigger_shipment_notification
from rl_feedback_system import (
    record_agent_action, record_action_outcome, get_agent_recommendations,
    ActionType, rl_feedback_system
)

class RLEnhancedRestockAgent:
    """Restock agent enhanced with RL feedback"""
    
    def __init__(self):
        self.agent_name = "rl_restock_agent"
        self.base_confidence = 0.7
        self.learning_enabled = True
    
    def analyze_inventory_with_rl(self) -> List[Dict]:
        """Analyze inventory with RL-enhanced decision making"""
        print(f"[{self.agent_name}] Starting RL-enhanced inventory analysis...")
        
        # Get RL recommendations
        recommendations = get_agent_recommendations(self.agent_name)
        recommended_params = recommendations.get("recommended_parameters", {})
        
        # Adjust confidence threshold based on RL feedback
        confidence_threshold = recommended_params.get("confidence_threshold", self.base_confidence)
        risk_tolerance = recommended_params.get("risk_tolerance", 0.5)
        
        print(f"[{self.agent_name}] Using RL-adjusted confidence threshold: {confidence_threshold:.2f}")
        
        # Simulate inventory analysis
        low_stock_items = [
            {"product_id": "A101", "name": "Wireless Mouse", "current_stock": 5, "reorder_point": 15, "demand_forecast": 25},
            {"product_id": "B205", "name": "USB Cable", "current_stock": 8, "reorder_point": 20, "demand_forecast": 40},
            {"product_id": "C330", "name": "Keyboard", "current_stock": 3, "reorder_point": 10, "demand_forecast": 18}
        ]
        
        restock_decisions = []
        
        for item in low_stock_items:
            # Calculate confidence based on multiple factors
            stock_urgency = (item["reorder_point"] - item["current_stock"]) / item["reorder_point"]
            demand_confidence = min(1.0, item["demand_forecast"] / (item["reorder_point"] * 2))
            
            # RL-enhanced confidence calculation
            base_confidence = (stock_urgency + demand_confidence) / 2
            rl_adjusted_confidence = base_confidence * (1 + risk_tolerance * 0.2)
            
            if rl_adjusted_confidence >= confidence_threshold:
                # Calculate optimal restock quantity using RL insights
                safety_multiplier = 1.2 + (risk_tolerance * 0.3)
                restock_quantity = int(item["demand_forecast"] * safety_multiplier)
                
                # Record RL action
                action_context = {
                    "current_stock": item["current_stock"],
                    "reorder_point": item["reorder_point"],
                    "demand_forecast": item["demand_forecast"]
                }
                
                action_id = record_agent_action(
                    self.agent_name,
                    "restock_decision",
                    {
                        "product_id": item["product_id"],
                        "quantity": restock_quantity,
                        "expected_cost": restock_quantity * 15,  # Estimated unit cost
                        "expected_time": 24
                    },
                    rl_adjusted_confidence,
                    action_context
                )
                
                decision = {
                    "product_id": item["product_id"],
                    "product_name": item["name"],
                    "current_stock": item["current_stock"],
                    "restock_quantity": restock_quantity,
                    "confidence": rl_adjusted_confidence,
                    "action_id": action_id,
                    "rl_enhanced": True
                }
                
                restock_decisions.append(decision)
                
                # Trigger EMS notification
                trigger_restock_alert(
                    item["product_id"],
                    item["name"],
                    item["current_stock"],
                    restock_quantity
                )
                
                print(f"[{self.agent_name}] RL Decision: Restock {item['name']} - Qty: {restock_quantity}, Confidence: {rl_adjusted_confidence:.2f}")
        
        return restock_decisions
    
    def simulate_restock_outcomes(self, decisions: List[Dict]):
        """Simulate outcomes and provide RL feedback"""
        print(f"[{self.agent_name}] Simulating restock outcomes for RL feedback...")
        
        for decision in decisions:
            # Simulate outcome after some time
            time.sleep(0.5)  # Simulate processing time
            
            # Random outcome simulation
            success_probability = decision["confidence"] * 0.9  # Higher confidence = higher success
            success = random.random() < success_probability
            
            # Simulate costs and timing
            expected_cost = decision["restock_quantity"] * 15
            actual_cost = expected_cost * random.uniform(0.9, 1.2)  # ±20% variance
            
            expected_time = 24
            actual_time = expected_time * random.uniform(0.8, 1.5)  # Timing variance
            
            # Customer satisfaction (affected by stock availability)
            customer_satisfaction = 4.5 if success else 2.5
            
            # Business impact (revenue protection)
            business_impact = 7.0 if success else 3.0
            
            # Record outcome for RL learning
            record_action_outcome(
                decision["action_id"],
                success,
                actual_cost,
                expected_cost,
                actual_time,
                expected_time,
                customer_satisfaction,
                business_impact
            )
            
            status = "SUCCESS" if success else "FAILED"
            print(f"[{self.agent_name}] Outcome for {decision['product_name']}: {status}")

class RLEnhancedProcurementAgent:
    """Procurement agent enhanced with RL feedback"""
    
    def __init__(self):
        self.agent_name = "rl_procurement_agent"
        self.base_confidence = 0.75
    
    def process_purchase_orders_with_rl(self, restock_decisions: List[Dict]) -> List[Dict]:
        """Process purchase orders with RL enhancement"""
        print(f"[{self.agent_name}] Processing purchase orders with RL feedback...")
        
        # Get RL recommendations
        recommendations = get_agent_recommendations(self.agent_name)
        recommended_params = recommendations.get("recommended_parameters", {})
        
        supplier_database = {
            "A101": {"supplier": "TechParts Co", "email": "orders@techparts.com", "lead_time": 3, "reliability": 0.9},
            "B205": {"supplier": "Cable Solutions", "email": "sales@cablesolutions.com", "lead_time": 2, "reliability": 0.85},
            "C330": {"supplier": "Input Devices Ltd", "email": "procurement@inputdevices.com", "lead_time": 4, "reliability": 0.95}
        }
        
        purchase_orders = []
        
        for decision in restock_decisions:
            product_id = decision["product_id"]
            if product_id in supplier_database:
                supplier_info = supplier_database[product_id]
                
                # RL-enhanced supplier selection confidence
                reliability_factor = supplier_info["reliability"]
                lead_time_factor = 1.0 / (supplier_info["lead_time"] / 3.0)  # Normalize to 3 days
                
                confidence = (reliability_factor + lead_time_factor) / 2
                confidence *= recommended_params.get("optimization_weight", 1.0)
                
                # Generate PO number
                po_number = f"PO-{datetime.now().strftime('%Y%m%d')}-{random.randint(1000, 9999)}"
                
                # Record RL action
                action_id = record_agent_action(
                    self.agent_name,
                    "procurement_order",
                    {
                        "supplier": supplier_info["supplier"],
                        "product_id": product_id,
                        "quantity": decision["restock_quantity"],
                        "expected_cost": decision["restock_quantity"] * 15,
                        "expected_time": supplier_info["lead_time"] * 24
                    },
                    confidence,
                    {"supplier_reliability": reliability_factor, "lead_time": supplier_info["lead_time"]}
                )
                
                # Create purchase order
                po = {
                    "po_number": po_number,
                    "product_id": product_id,
                    "product_name": decision["product_name"],
                    "quantity": decision["restock_quantity"],
                    "supplier": supplier_info["supplier"],
                    "supplier_email": supplier_info["email"],
                    "unit_cost": 15.0,
                    "total_cost": decision["restock_quantity"] * 15.0,
                    "expected_delivery": (datetime.now() + timedelta(days=supplier_info["lead_time"])).strftime("%Y-%m-%d"),
                    "confidence": confidence,
                    "action_id": action_id
                }
                
                purchase_orders.append(po)
                
                # Trigger EMS notification
                trigger_purchase_order(
                    supplier_info["email"],
                    po_number,
                    decision["product_name"],
                    decision["restock_quantity"],
                    15.0,
                    po["total_cost"],
                    po["expected_delivery"]
                )
                
                print(f"[{self.agent_name}] RL-Enhanced PO: {po_number} to {supplier_info['supplier']}")
        
        return purchase_orders
    
    def simulate_procurement_outcomes(self, purchase_orders: List[Dict]):
        """Simulate procurement outcomes for RL feedback"""
        print(f"[{self.agent_name}] Simulating procurement outcomes...")
        
        for po in purchase_orders:
            time.sleep(0.3)
            
            # Success based on confidence and random factors
            success = random.random() < (po["confidence"] * 0.85)
            
            # Cost and time simulation
            actual_cost = po["total_cost"] * random.uniform(0.95, 1.1)
            expected_time = 72  # 3 days average
            actual_time = expected_time * random.uniform(0.8, 1.4)
            
            customer_satisfaction = 4.2 if success else 2.8
            business_impact = 6.5 if success else 4.0
            
            record_action_outcome(
                po["action_id"],
                success,
                actual_cost,
                po["total_cost"],
                actual_time,
                expected_time,
                customer_satisfaction,
                business_impact
            )
            
            print(f"[{self.agent_name}] PO {po['po_number']}: {'SUCCESS' if success else 'DELAYED'}")

class RLEnhancedDeliveryAgent:
    """Delivery agent enhanced with RL feedback"""
    
    def __init__(self):
        self.agent_name = "rl_delivery_agent"
        self.base_confidence = 0.8
    
    def process_shipments_with_rl(self) -> List[Dict]:
        """Process shipments with RL enhancement"""
        print(f"[{self.agent_name}] Processing shipments with RL optimization...")
        
        # Get RL recommendations
        recommendations = get_agent_recommendations(self.agent_name)
        
        # Simulate pending orders
        pending_orders = [
            {"order_id": "ORD-12345", "customer_email": "john.doe@example.com", "priority": "high"},
            {"order_id": "ORD-12346", "customer_email": "jane.smith@example.com", "priority": "medium"},
            {"order_id": "ORD-12347", "customer_email": "bob.wilson@example.com", "priority": "low"}
        ]
        
        courier_options = [
            {"name": "FastShip Express", "reliability": 0.95, "speed": 1.2, "cost_factor": 1.1},
            {"name": "QuickDelivery Co", "reliability": 0.88, "speed": 1.0, "cost_factor": 1.0},
            {"name": "EconoShip", "reliability": 0.82, "speed": 0.8, "cost_factor": 0.9}
        ]
        
        shipments = []
        
        for order in pending_orders:
            # RL-enhanced courier selection
            priority_weight = {"high": 1.2, "medium": 1.0, "low": 0.8}[order["priority"]]
            
            best_courier = None
            best_score = 0
            
            for courier in courier_options:
                # Score based on reliability, speed, and cost
                score = (courier["reliability"] * 0.4 + 
                        courier["speed"] * 0.4 + 
                        (2.0 - courier["cost_factor"]) * 0.2) * priority_weight
                
                if score > best_score:
                    best_score = score
                    best_courier = courier
            
            # Generate tracking number
            tracking_number = f"FS{random.randint(100000000, 999999999)}"
            
            # Record RL action
            action_id = record_agent_action(
                self.agent_name,
                "delivery_routing",
                {
                    "order_id": order["order_id"],
                    "courier": best_courier["name"],
                    "expected_cost": 25.0,
                    "expected_time": 48
                },
                best_score,
                {"priority": order["priority"], "courier_reliability": best_courier["reliability"]}
            )
            
            shipment = {
                "order_id": order["order_id"],
                "customer_email": order["customer_email"],
                "tracking_number": tracking_number,
                "courier": best_courier["name"],
                "estimated_delivery": (datetime.now() + timedelta(days=2)).strftime("%Y-%m-%d"),
                "confidence": best_score,
                "action_id": action_id
            }
            
            shipments.append(shipment)
            
            # Trigger EMS notification
            trigger_shipment_notification(
                order["customer_email"],
                order["order_id"],
                tracking_number,
                best_courier["name"],
                shipment["estimated_delivery"],
                f"https://tracking.example.com/{tracking_number}"
            )
            
            print(f"[{self.agent_name}] RL-Optimized shipment: {order['order_id']} via {best_courier['name']}")
        
        return shipments
    
    def simulate_delivery_outcomes(self, shipments: List[Dict]):
        """Simulate delivery outcomes for RL feedback"""
        print(f"[{self.agent_name}] Simulating delivery outcomes...")
        
        for shipment in shipments:
            time.sleep(0.2)
            
            # Success probability based on confidence
            success = random.random() < (shipment["confidence"] * 0.9)
            
            actual_cost = 25.0 * random.uniform(0.9, 1.15)
            expected_time = 48
            actual_time = expected_time * random.uniform(0.7, 1.3)
            
            customer_satisfaction = 4.7 if success else 3.2
            business_impact = 5.5 if success else 4.2
            
            record_action_outcome(
                shipment["action_id"],
                success,
                actual_cost,
                25.0,
                actual_time,
                expected_time,
                customer_satisfaction,
                business_impact
            )
            
            print(f"[{self.agent_name}] Delivery {shipment['order_id']}: {'ON TIME' if success else 'DELAYED'}")

def run_rl_integrated_workflow():
    """Run the complete RL-integrated workflow"""
    print("=" * 60)
    print("NOOPUR'S RISHABH RL-INTEGRATED WORKFLOW")
    print("=" * 60)
    
    # Initialize RL-enhanced agents
    restock_agent = RLEnhancedRestockAgent()
    procurement_agent = RLEnhancedProcurementAgent()
    delivery_agent = RLEnhancedDeliveryAgent()
    
    # Step 1: RL-Enhanced Inventory Analysis
    print("\n[STEP 1] RL-Enhanced Inventory Analysis")
    restock_decisions = restock_agent.analyze_inventory_with_rl()
    
    # Step 2: RL-Enhanced Procurement
    print("\n[STEP 2] RL-Enhanced Procurement Processing")
    purchase_orders = procurement_agent.process_purchase_orders_with_rl(restock_decisions)
    
    # Step 3: RL-Enhanced Delivery Management
    print("\n[STEP 3] RL-Enhanced Delivery Management")
    shipments = delivery_agent.process_shipments_with_rl()
    
    # Step 4: Simulate outcomes for RL learning
    print("\n[STEP 4] Simulating Outcomes for RL Learning")
    restock_agent.simulate_restock_outcomes(restock_decisions)
    procurement_agent.simulate_procurement_outcomes(purchase_orders)
    delivery_agent.simulate_delivery_outcomes(shipments)
    
    # Step 5: Display RL Analytics
    print("\n[STEP 5] RL Learning Analytics")
    from rl_feedback_system import get_rl_analytics
    analytics = get_rl_analytics()
    
    print(f"Total RL Actions: {analytics['total_actions']}")
    print(f"Average Reward: {analytics['average_reward']:.2f}")
    print(f"Learning Status: {analytics['learning_progress']['status']}")
    
    print("\nAgent Performance Rankings:")
    for i, agent in enumerate(analytics['agent_rankings'][:3], 1):
        print(f"  {i}. {agent['agent_name']}: {agent['average_reward']:.2f} avg reward")
    
    # Save learning data
    rl_feedback_system.optimizer.save_learning_data()
    
    print("\n" + "=" * 60)
    print("RL-INTEGRATED WORKFLOW COMPLETED")
    print("✓ All agents now learning and optimizing with RL feedback")
    print("✓ Reward/penalty loops active for continuous improvement")
    print("✓ Learning data saved for future optimization")
    print("=" * 60)

if __name__ == "__main__":
    run_rl_integrated_workflow()