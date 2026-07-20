#!/usr/bin/env python3
"""
Notification System for AI Agent Logistics
Handles alerts, notifications, and real-time monitoring
"""

import json
import uuid
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from database.service import DatabaseService
from database.models import Alert, KPIMetric, NotificationLog

class NotificationSystem:
    """Comprehensive notification and alerting system"""
    
    def __init__(self):
        self.alert_thresholds = {
            'stock_critical': 0,      # Out of stock
            'stock_low': 0.5,         # Below 50% of reorder point
            'delivery_delay': 24,     # Hours without status update
            'review_backlog': 5,      # Pending reviews threshold
            'automation_rate': 60     # Minimum automation rate %
        }
    
    def check_stock_alerts(self) -> List[Dict]:
        """Check for stock-related alerts"""
        alerts = []
        
        with DatabaseService() as db_service:
            inventory = db_service.get_inventory()
            low_stock = db_service.get_low_stock_items()
            
            for item in inventory:
                product_id = item['ProductID']
                current_stock = item['CurrentStock']
                reorder_point = item['ReorderPoint']
                
                # Critical: Out of stock
                if current_stock == 0:
                    alerts.append({
                        'type': 'stockout',
                        'severity': 'critical',
                        'title': f'STOCKOUT: {product_id}',
                        'message': f'Product {product_id} is completely out of stock. Immediate action required.',
                        'entity_type': 'product',
                        'entity_id': product_id,
                        'data': {
                            'current_stock': current_stock,
                            'reorder_point': reorder_point
                        }
                    })
                
                # High: Very low stock
                elif current_stock <= reorder_point * self.alert_thresholds['stock_low']:
                    alerts.append({
                        'type': 'low_stock',
                        'severity': 'high',
                        'title': f'LOW STOCK: {product_id}',
                        'message': f'Product {product_id} stock is critically low ({current_stock} units, reorder at {reorder_point}).',
                        'entity_type': 'product',
                        'entity_id': product_id,
                        'data': {
                            'current_stock': current_stock,
                            'reorder_point': reorder_point
                        }
                    })
        
        return alerts
    
    def check_delivery_alerts(self) -> List[Dict]:
        """Check for delivery-related alerts"""
        alerts = []
        
        with DatabaseService() as db_service:
            shipments = db_service.get_shipments()
            
            for shipment in shipments:
                if shipment['status'] in ['delivered', 'cancelled']:
                    continue
                
                created_at = shipment.get('created_at')
                if not created_at:
                    continue
                
                try:
                    created_time = datetime.fromisoformat(created_at.replace('Z', '+00:00'))
                    hours_elapsed = (datetime.now() - created_time.replace(tzinfo=None)).total_seconds() / 3600
                    
                    # Alert for shipments stuck in created status
                    if shipment['status'] == 'created' and hours_elapsed > self.alert_thresholds['delivery_delay']:
                        alerts.append({
                            'type': 'delivery_delay',
                            'severity': 'medium',
                            'title': f'SHIPMENT DELAY: {shipment["tracking_number"]}',
                            'message': f'Shipment for Order #{shipment["order_id"]} has been in created status for {hours_elapsed:.1f} hours.',
                            'entity_type': 'shipment',
                            'entity_id': shipment['tracking_number'],
                            'data': {
                                'order_id': shipment['order_id'],
                                'status': shipment['status'],
                                'hours_elapsed': hours_elapsed
                            }
                        })
                    
                    # Alert for overdue deliveries
                    estimated_delivery = shipment.get('estimated_delivery')
                    if estimated_delivery and shipment['status'] not in ['delivered']:
                        est_time = datetime.fromisoformat(estimated_delivery.replace('Z', '+00:00'))
                        if datetime.now() > est_time.replace(tzinfo=None):
                            alerts.append({
                                'type': 'delivery_overdue',
                                'severity': 'high',
                                'title': f'OVERDUE DELIVERY: {shipment["tracking_number"]}',
                                'message': f'Shipment for Order #{shipment["order_id"]} is overdue (estimated: {estimated_delivery[:10]}).',
                                'entity_type': 'shipment',
                                'entity_id': shipment['tracking_number'],
                                'data': {
                                    'order_id': shipment['order_id'],
                                    'estimated_delivery': estimated_delivery,
                                    'current_status': shipment['status']
                                }
                            })
                
                except (ValueError, TypeError) as e:
                    continue
        
        return alerts
    
    def check_system_alerts(self) -> List[Dict]:
        """Check for system-related alerts"""
        alerts = []
        
        with DatabaseService() as db_service:
            # Check pending reviews
            pending_reviews = db_service.get_pending_reviews()
            if len(pending_reviews) > self.alert_thresholds['review_backlog']:
                alerts.append({
                    'type': 'review_backlog',
                    'severity': 'medium',
                    'title': 'HIGH REVIEW BACKLOG',
                    'message': f'{len(pending_reviews)} items are pending human review. Consider reviewing to maintain automation efficiency.',
                    'entity_type': 'system',
                    'entity_id': 'review_queue',
                    'data': {
                        'pending_count': len(pending_reviews),
                        'threshold': self.alert_thresholds['review_backlog']
                    }
                })
            
            # Check automation rate
            metrics = db_service.get_performance_metrics(days=1)
            automation_rate = metrics.get('automation_rate', 0)
            if automation_rate < self.alert_thresholds['automation_rate']:
                alerts.append({
                    'type': 'low_automation',
                    'severity': 'medium',
                    'title': 'LOW AUTOMATION RATE',
                    'message': f'System automation rate is {automation_rate:.1f}%, below threshold of {self.alert_thresholds["automation_rate"]}%.',
                    'entity_type': 'system',
                    'entity_id': 'automation',
                    'data': {
                        'current_rate': automation_rate,
                        'threshold': self.alert_thresholds['automation_rate']
                    }
                })
        
        return alerts
    
    def create_alert(self, alert_data: Dict) -> str:
        """Create and store an alert"""
        alert_id = f"ALERT_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        with DatabaseService() as db_service:
            # Store alert (simplified - in production would use proper ORM)
            db_service.log_agent_action(
                action="alert_created",
                details=f"Alert created: {json.dumps(alert_data)}"
            )
        
        return alert_id
    
    def send_notification(self, notification_type: str, recipient: str, subject: str, message: str) -> bool:
        """Send notification (console/email/SMS simulation)"""
        notification_id = f"NOTIF_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{uuid.uuid4().hex[:6]}"
        
        try:
            # Console notification (for demo)
            if notification_type == 'console':
                print(f"\n🚨 NOTIFICATION: {subject}")
                print(f"📧 To: {recipient}")
                print(f"💬 Message: {message}")
                print(f"⏰ Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
            
            # Email simulation
            elif notification_type == 'email':
                print(f"\n📧 EMAIL SENT")
                print(f"To: {recipient}")
                print(f"Subject: {subject}")
                print(f"Body: {message}")
                print(f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
            
            # SMS simulation
            elif notification_type == 'sms':
                print(f"\n📱 SMS SENT")
                print(f"To: {recipient}")
                print(f"Message: {message[:160]}...")  # SMS character limit
                print(f"Sent: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
                print("-" * 50)
            
            # Log notification
            with DatabaseService() as db_service:
                db_service.log_agent_action(
                    action="notification_sent",
                    details=f"Notification sent: {notification_type} to {recipient}"
                )
            
            return True
            
        except Exception as e:
            print(f"❌ Failed to send notification: {e}")
            return False
    
    def calculate_kpis(self) -> Dict:
        """Calculate and store KPI metrics"""
        with DatabaseService() as db_service:
            # Get data for KPI calculations
            orders = db_service.get_orders()
            shipments = db_service.get_shipments()
            inventory = db_service.get_inventory()
            low_stock = db_service.get_low_stock_items()
            performance = db_service.get_performance_metrics(days=1)
            
            # Calculate KPIs
            kpis = {
                'total_orders': len(orders),
                'active_shipments': len([s for s in shipments if s['status'] not in ['delivered', 'cancelled']]),
                'delivery_rate': (len([s for s in shipments if s['status'] == 'delivered']) / len(shipments) * 100) if shipments else 0,
                'stock_health': ((len(inventory) - len(low_stock)) / len(inventory) * 100) if inventory else 100,
                'automation_rate': performance.get('automation_rate', 0),
                'pending_reviews': len(db_service.get_pending_reviews())
            }
            
            # Store KPIs (simplified)
            db_service.log_agent_action(
                action="kpi_calculated",
                details=f"KPIs calculated: {json.dumps(kpis)}"
            )
            
            return kpis
    
    def run_monitoring_cycle(self) -> Dict:
        """Run complete monitoring and alerting cycle"""
        print("🔍 Starting Notification System Monitoring Cycle")
        print("=" * 60)
        
        results = {
            'alerts_created': 0,
            'notifications_sent': 0,
            'kpis_calculated': 0,
            'errors': []
        }
        
        try:
            # Check all alert types
            all_alerts = []
            all_alerts.extend(self.check_stock_alerts())
            all_alerts.extend(self.check_delivery_alerts())
            all_alerts.extend(self.check_system_alerts())
            
            # Process alerts
            for alert in all_alerts:
                alert_id = self.create_alert(alert)
                results['alerts_created'] += 1
                
                # Send notifications based on severity
                if alert['severity'] in ['critical', 'high']:
                    success = self.send_notification(
                        'console',
                        'operations@company.com',
                        alert['title'],
                        alert['message']
                    )
                    if success:
                        results['notifications_sent'] += 1
                
                print(f"🚨 {alert['severity'].upper()}: {alert['title']}")
                print(f"   {alert['message']}")
            
            # Calculate KPIs
            kpis = self.calculate_kpis()
            results['kpis_calculated'] = len(kpis)
            
            print(f"\n📊 KPI Summary:")
            for key, value in kpis.items():
                if isinstance(value, float):
                    print(f"   {key}: {value:.1f}")
                else:
                    print(f"   {key}: {value}")
            
            print("=" * 60)
            print("✅ Monitoring cycle completed")
            print(f"📊 Results: {results['alerts_created']} alerts, {results['notifications_sent']} notifications")
            
            return results
            
        except Exception as e:
            error_msg = f"Monitoring cycle error: {str(e)}"
            results['errors'].append(error_msg)
            print(f"❌ {error_msg}")
            return results

def run_notification_system():
    """Main function to run notification system"""
    system = NotificationSystem()
    return system.run_monitoring_cycle()

if __name__ == "__main__":
    print("🚨 AI Agent Notification System")
    print("Real-time Monitoring and Alerting")
    print()
    
    results = run_notification_system()
    
    print(f"\n📈 Final Results:")
    print(f"   - Alerts Created: {results['alerts_created']}")
    print(f"   - Notifications Sent: {results['notifications_sent']}")
    print(f"   - KPIs Calculated: {results['kpis_calculated']}")
    print(f"   - Errors: {len(results['errors'])}")
    
    if results['errors']:
        print(f"\n⚠️  Errors encountered:")
        for error in results['errors']:
            print(f"   - {error}")
    
    print(f"\n🚀 Notification system cycle complete!")
