"""
Event Broker for BHIV Integrator Core
Handles event-driven communication between Logistics, CRM, and Task Management systems
"""

from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from typing import Dict, Any, List, Optional
import asyncio
import json
import uuid
from datetime import datetime
import requests
import aio_pika
import pika
from config.settings import settings
from unified_logging.logger import UnifiedLogger

router = APIRouter()
logger = UnifiedLogger()

class EventMessage(BaseModel):
    event_type: str
    source_system: str
    target_systems: List[str]
    payload: Dict[str, Any]
    event_id: Optional[str] = None
    timestamp: Optional[str] = None
    priority: str = "normal"
    correlation_id: Optional[str] = None

class Subscription(BaseModel):
    system_name: str
    event_types: List[str]
    webhook_url: str
    active: bool = True

# In-memory storage (replace with Redis/DB in production)
event_store = []
subscriptions = {}

class EventBroker:
    def __init__(self):
        self.subscriptions = subscriptions
        self.event_store = event_store
        self.logger = logger
        self.rabbitmq_connection = None
        self.rabbitmq_channel = None
        self.rabbitmq_exchange = None

    async def start(self):
        """Start the event broker"""
        print("🎯 Event Broker starting...")
        # Initialize RabbitMQ connection
        await self._initialize_rabbitmq()
        # Initialize default subscriptions
        await self._initialize_subscriptions()
        # Start consumer tasks
        await self._start_consumers()

    async def stop(self):
        """Stop the event broker"""
        print("🛑 Event Broker stopping...")
        if self.rabbitmq_connection:
            await self.rabbitmq_connection.close()

    async def _initialize_subscriptions(self):
        """Initialize default system subscriptions"""
        default_subs = {
            "logistics": {
                "system_name": "logistics",
                "event_types": ["order_created", "delivery_completed", "inventory_low"],
                "webhook_url": f"{settings['logistics_base_url']}/webhooks/events",
                "active": True
            },
            "crm": {
                "system_name": "crm",
                "event_types": ["lead_created", "opportunity_updated", "account_changed"],
                "webhook_url": f"{settings['crm_base_url']}/webhooks/events",
                "active": True
            },
            "task_manager": {
                "system_name": "task_manager",
                "event_types": ["task_created", "task_completed", "task_escalated"],
                "webhook_url": f"{settings['task_base_url']}/webhooks/events",
                "active": True
            },
            "bhiv_core": {
                "system_name": "bhiv_core",
                "event_types": ["agent_decision", "knowledge_retrieved"],
                "webhook_url": f"{settings['bhiv_core_url']}/webhooks/events",
                "active": True
            }
        }

        for name, sub in default_subs.items():
            self.subscriptions[name] = sub
            print(f"📡 Registered subscription for {name}")
            # Declare queue for each system
            await self._declare_queue(name)

    async def publish_event(self, event: EventMessage) -> Dict[str, Any]:
        """Publish an event to subscribed systems"""
        if not event.event_id:
            event.event_id = str(uuid.uuid4())
        if not event.timestamp:
            event.timestamp = datetime.now().isoformat()
        if not event.correlation_id:
            event.correlation_id = event.event_id

        # Store event
        event_dict = event.dict()
        self.event_store.append(event_dict)

        # Log event
        await self.logger.log_event({
            "event_id": event.event_id,
            "event_type": event.event_type,
            "source_system": event.source_system,
            "target_systems": event.target_systems,
            "payload": event.payload,
            "timestamp": event.timestamp,
            "correlation_id": event.correlation_id,
            "dhi_score": self._calculate_dhi_score(event),
            "compliance_flag": self._check_compliance(event)
        })

        # Trigger event processing
        await self._process_event_triggers(event)

        # Publish to RabbitMQ
        await self._publish_to_rabbitmq(event)

        # Notify subscribers via HTTP (fallback)
        await self._notify_subscribers(event)

        return {
            "event_id": event.event_id,
            "status": "published",
            "subscribers_notified": len(event.target_systems)
        }

    async def _process_event_triggers(self, event: EventMessage):
        """Process event triggers based on configuration"""
        triggers = settings.get("event_triggers", {})
        trigger_actions = triggers.get(event.event_type, [])

        for action in trigger_actions:
            await self._execute_trigger_action(event, action)

    async def _execute_trigger_action(self, event: EventMessage, action: str):
        """Execute a trigger action"""
        print(f"🎯 Executing trigger: {action} for event {event.event_type}")

        # Example trigger actions
        if action == "create_crm_lead":
            await self._create_crm_lead_from_order(event)
        elif action == "create_task":
            await self._create_task_from_event(event)
        elif action == "escalate_task":
            await self._escalate_task(event)
        elif action == "update_crm_opportunity":
            await self._update_crm_opportunity(event)
        elif action == "compliance_check":
            await self._perform_compliance_check(event)
        elif action == "send_slack_alert":
            await self._send_slack_alert(event)
        elif action == "send_teams_alert":
            await self._send_teams_alert(event)

    async def _create_crm_lead_from_order(self, event: EventMessage):
        """Create CRM lead from order event"""
        try:
            crm_payload = {
                "lead_source": "order",
                "company": event.payload.get("customer_name", "Unknown"),
                "budget": event.payload.get("order_value", 0),
                "notes": f"Auto-created from order {event.payload.get('order_id')}"
            }

            # Call CRM API
            response = requests.post(
                f"{settings['crm_base_url']}/leads",
                json=crm_payload,
                timeout=5
            )
            print(f"✅ CRM Lead created: {response.status_code}")

        except Exception as e:
            print(f"❌ Failed to create CRM lead: {str(e)}")

    async def _create_task_from_event(self, event: EventMessage):
        """Create task from event"""
        try:
            task_payload = {
                "title": f"Follow up on {event.event_type}",
                "description": f"Auto-created task for {event.event_type}",
                "priority": "medium",
                "assignee": "system",
                "reference_id": event.event_id
            }

            response = requests.post(
                f"{settings['task_base_url']}/tasks",
                json=task_payload,
                timeout=5
            )
            print(f"✅ Task created: {response.status_code}")

        except Exception as e:
            print(f"❌ Failed to create task: {str(e)}")

    async def _escalate_task(self, event: EventMessage):
        """Escalate existing task"""
        try:
            # Find related task from event payload
            task_id = event.payload.get("task_id")
            if not task_id:
                print("⚠️ No task_id found in event payload for escalation")
                return

            escalation_payload = {
                "status": "escalated",
                "priority": "high",
                "escalation_reason": f"Triggered by {event.event_type}",
                "escalation_timestamp": datetime.now().isoformat()
            }

            # Update task via Task API
            response = requests.put(
                f"{settings['task_base_url']}/tasks/{task_id}",
                json=escalation_payload,
                timeout=5
            )

            if response.status_code == 200:
                print(f"✅ Task {task_id} escalated due to {event.event_type}")
            else:
                print(f"⚠️ Task escalation failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Task escalation error: {str(e)}")

    async def _update_crm_opportunity(self, event: EventMessage):
        """Update CRM opportunity"""
        try:
            # Find opportunity from event payload
            opportunity_id = event.payload.get("opportunity_id")
            if not opportunity_id:
                print("⚠️ No opportunity_id found in event payload")
                return

            update_payload = {
                "last_activity": datetime.now().isoformat(),
                "last_activity_type": event.event_type,
                "notes": f"Updated due to {event.event_type} event"
            }

            # Add specific updates based on event type
            if event.event_type == "delivery_completed":
                update_payload["stage"] = "closed_won"
                update_payload["close_date"] = datetime.now().isoformat()
            elif event.event_type == "task_completed":
                update_payload["probability"] = 90

            # Update opportunity via CRM API
            response = requests.put(
                f"{settings['crm_base_url']}/opportunities/{opportunity_id}",
                json=update_payload,
                timeout=5
            )

            if response.status_code == 200:
                print(f"✅ Opportunity {opportunity_id} updated due to {event.event_type}")
            else:
                print(f"⚠️ Opportunity update failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Opportunity update error: {str(e)}")

    async def _perform_compliance_check(self, event: EventMessage):
        """Perform compliance check"""
        try:
            from compliance.compliance_hooks import ComplianceHooks
            compliance = ComplianceHooks()

            # Prepare compliance check data
            compliance_data = {
                "event_type": event.event_type,
                "source_system": event.source_system,
                "payload": event.payload,
                "timestamp": event.timestamp,
                "event_id": event.event_id
            }

            # Perform compliance check
            result = await compliance.check_transaction_compliance(compliance_data)

            if result.get("compliant", False):
                print(f"✅ Compliance check passed for event {event.event_id}")
            else:
                print(f"⚠️ Compliance check failed for event {event.event_id}: {result.get('message', 'Unknown')}")

                # Trigger compliance violation event
                await self.publish_event({
                    "event_type": "compliance_violation",
                    "source_system": "event_broker",
                    "target_systems": ["compliance", "task_manager"],
                    "payload": {
                        "original_event": event.dict(),
                        "violation_details": result
                    },
                    "priority": "high"
                })

        except Exception as e:
            print(f"❌ Compliance check error: {str(e)}")

    async def _send_slack_alert(self, event: EventMessage):
        """Send alert to Slack"""
        try:
            slack_webhook = settings.get("slack_webhook_url")
            if not slack_webhook:
                print("⚠️ Slack webhook URL not configured")
                return

            alert_message = {
                "text": f"🚨 BHIV Alert: {event.event_type}",
                "blocks": [
                    {
                        "type": "header",
                        "text": {
                            "type": "plain_text",
                            "text": f"🚨 {event.event_type.replace('_', ' ').title()}"
                        }
                    },
                    {
                        "type": "section",
                        "fields": [
                            {
                                "type": "mrkdwn",
                                "text": f"*Source:* {event.source_system}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Priority:* {event.priority}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Event ID:* {event.event_id}"
                            },
                            {
                                "type": "mrkdwn",
                                "text": f"*Time:* {event.timestamp}"
                            }
                        ]
                    },
                    {
                        "type": "section",
                        "text": {
                            "type": "mrkdwn",
                            "text": f"*Details:* {json.dumps(event.payload, indent=2)}"
                        }
                    }
                ]
            }

            response = requests.post(slack_webhook, json=alert_message, timeout=5)
            if response.status_code == 200:
                print(f"✅ Slack alert sent for event {event.event_id}")
            else:
                print(f"⚠️ Slack alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Slack alert error: {str(e)}")

    async def _send_teams_alert(self, event: EventMessage):
        """Send alert to Microsoft Teams"""
        try:
            teams_webhook = settings.get("teams_webhook_url")
            if not teams_webhook:
                print("⚠️ Teams webhook URL not configured")
                return

            alert_message = {
                "@type": "MessageCard",
                "@context": "http://schema.org/extensions",
                "themeColor": "0076D7" if event.priority == "high" else "FFA500",
                "summary": f"BHIV Alert: {event.event_type}",
                "sections": [
                    {
                        "activityTitle": f"🚨 {event.event_type.replace('_', ' ').title()}",
                        "activitySubtitle": f"Source: {event.source_system} | Priority: {event.priority}",
                        "facts": [
                            {
                                "name": "Event ID:",
                                "value": event.event_id
                            },
                            {
                                "name": "Timestamp:",
                                "value": event.timestamp
                            },
                            {
                                "name": "Correlation ID:",
                                "value": event.correlation_id
                            }
                        ],
                        "text": f"**Payload:**\n```\n{json.dumps(event.payload, indent=2)}\n```"
                    }
                ],
                "potentialAction": [
                    {
                        "@type": "OpenUri",
                        "name": "View Details",
                        "targets": [
                            {
                                "os": "default",
                                "uri": f"http://localhost:8006/events?event_id={event.event_id}"
                            }
                        ]
                    }
                ]
            }

            response = requests.post(teams_webhook, json=alert_message, timeout=5)
            if response.status_code == 200:
                print(f"✅ Teams alert sent for event {event.event_id}")
            else:
                print(f"⚠️ Teams alert failed: {response.status_code}")

        except Exception as e:
            print(f"❌ Teams alert error: {str(e)}")

    async def _notify_subscribers(self, event: EventMessage):
        """Notify subscribed systems"""
        notified = 0
        for system_name, subscription in self.subscriptions.items():
            if subscription["active"] and event.event_type in subscription["event_types"]:
                try:
                    response = requests.post(
                        subscription["webhook_url"],
                        json=event.dict(),
                        timeout=5
                    )
                    if response.status_code == 200:
                        notified += 1
                        print(f"📡 Notified {system_name}: {response.status_code}")
                    else:
                        print(f"⚠️ Failed to notify {system_name}: {response.status_code}")
                except Exception as e:
                    print(f"❌ Error notifying {system_name}: {str(e)}")

        print(f"📊 Event {event.event_id} notified {notified} subscribers")

    def _calculate_dhi_score(self, event: EventMessage) -> float:
        """Calculate DHI score for the event"""
        # Simplified DHI score calculation
        weights = settings.get("dhi_score_weights", {})
        base_score = 0.5  # Base score

        # Adjust based on event type priority
        if event.priority == "high":
            base_score += 0.3
        elif event.priority == "low":
            base_score -= 0.1

        # Adjust based on payload completeness
        if len(event.payload) > 5:
            base_score += 0.2

        return min(1.0, max(0.0, base_score))

    def _check_compliance(self, event: EventMessage) -> bool:
        """Check compliance flag for the event"""
        flags = settings.get("compliance_flags", {})
        # Simplified compliance check
        return flags.get("audit_trail", True)

    async def _initialize_rabbitmq(self):
        """Initialize RabbitMQ connection and exchange"""
        try:
            self.rabbitmq_connection = await aio_pika.connect_robust(settings["rabbitmq_url"])
            self.rabbitmq_channel = await self.rabbitmq_connection.channel()
            self.rabbitmq_exchange = await self.rabbitmq_channel.declare_exchange(
                settings["rabbitmq_exchange"], aio_pika.ExchangeType.TOPIC, durable=True
            )
            print("🐰 RabbitMQ connection established")
        except Exception as e:
            print(f"❌ Failed to initialize RabbitMQ: {str(e)}")

    async def _declare_queue(self, system_name: str):
        """Declare queue for a system"""
        try:
            queue_name = f"{settings['rabbitmq_queue_prefix']}{system_name}"
            queue = await self.rabbitmq_channel.declare_queue(queue_name, durable=True)

            # Bind queue to exchange with routing key
            await queue.bind(self.rabbitmq_exchange, routing_key=f"*.{system_name}")
            print(f"📋 Declared queue: {queue_name}")
        except Exception as e:
            print(f"❌ Failed to declare queue for {system_name}: {str(e)}")

    async def _start_consumers(self):
        """Start consumer tasks for each subscribed system"""
        for system_name in self.subscriptions.keys():
            asyncio.create_task(self._consume_messages(system_name))

    async def _consume_messages(self, system_name: str):
        """Consume messages for a specific system"""
        try:
            queue_name = f"{settings['rabbitmq_queue_prefix']}{system_name}"
            queue = await self.rabbitmq_channel.declare_queue(queue_name, durable=True)

            async with queue.iterator() as queue_iter:
                async for message in queue_iter:
                    async with message.process():
                        await self._process_message(system_name, message.body)
        except Exception as e:
            print(f"❌ Error consuming messages for {system_name}: {str(e)}")

    async def _process_message(self, system_name: str, message_body: bytes):
        """Process incoming message"""
        try:
            event_data = json.loads(message_body.decode())
            event = EventMessage(**event_data)

            # Process event triggers
            await self._process_event_triggers(event)

            # Log event
            await self.logger.log_event({
                "event_id": event.event_id,
                "event_type": event.event_type,
                "source_system": event.source_system,
                "target_systems": event.target_systems,
                "payload": event.payload,
                "timestamp": event.timestamp,
                "correlation_id": event.correlation_id,
                "dhi_score": self._calculate_dhi_score(event),
                "compliance_flag": self._check_compliance(event),
                "processed_by": system_name
            })

            print(f"📨 Processed event {event.event_id} for {system_name}")

        except Exception as e:
            print(f"❌ Error processing message: {str(e)}")

    async def _publish_to_rabbitmq(self, event: EventMessage):
        """Publish event to RabbitMQ"""
        try:
            message_body = json.dumps(event.dict()).encode()
            for target_system in event.target_systems:
                routing_key = f"{event.event_type}.{target_system}"
                await self.rabbitmq_exchange.publish(
                    aio_pika.Message(body=message_body, delivery_mode=aio_pika.DeliveryMode.PERSISTENT),
                    routing_key=routing_key
                )
            print(f"🐰 Published event {event.event_id} to RabbitMQ")
        except Exception as e:
            print(f"❌ Failed to publish to RabbitMQ: {str(e)}")

    async def subscribe(self, subscription: Subscription) -> Dict[str, Any]:
        """Subscribe a system to events"""
        self.subscriptions[subscription.system_name] = subscription.dict()
        return {"status": "subscribed", "system": subscription.system_name}

    async def get_events(self, system_name: str = None, event_type: str = None, limit: int = 50) -> List[Dict]:
        """Get events from store"""
        events = self.event_store[-limit:]  # Get last N events

        if system_name:
            events = [e for e in events if system_name in e.get("target_systems", [])]

        if event_type:
            events = [e for e in events if e.get("event_type") == event_type]

        return events

# API Endpoints
@router.post("/publish")
async def publish_event(event: EventMessage, background_tasks: BackgroundTasks):
    """Publish an event"""
    broker = EventBroker()
    result = await broker.publish_event(event)
    return result

@router.post("/subscribe")
async def subscribe_system(subscription: Subscription):
    """Subscribe a system to events"""
    broker = EventBroker()
    result = await broker.subscribe(subscription)
    return result

@router.get("/events")
async def get_events(system_name: str = None, event_type: str = None, limit: int = 50):
    """Get recent events"""
    broker = EventBroker()
    events = await broker.get_events(system_name, event_type, limit)
    return {"events": events, "count": len(events)}

@router.get("/subscriptions")
async def get_subscriptions():
    """Get all subscriptions"""
    return {"subscriptions": subscriptions}

@router.get("/health")
async def event_broker_health():
    """Event broker health check"""
    return {
        "status": "healthy",
        "subscribers": len(subscriptions),
        "events_stored": len(event_store),
        "timestamp": datetime.now().isoformat()
    }