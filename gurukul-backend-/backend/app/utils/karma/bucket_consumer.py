"""
Bucket Consumer for Karma Tracker

Polls the backend bucket for PRANA packets and processes them to update karma.
"""

import requests
import time
import logging
from typing import Dict, Any, List, Optional
from datetime import datetime

logger = logging.getLogger(__name__)


class BucketConsumer:
    """Consumes PRANA packets from the bucket and processes them for karma updates"""
    
    def __init__(
        self,
        bucket_url: str = "http://localhost:3000",
        karma_tracker_url: str = "http://localhost:8001",  # Karma Tracker runs on port 8001
        poll_interval: int = 5,
        batch_size: int = 10
    ):
        """
        Initialize bucket consumer.
        
        Args:
            bucket_url: Backend bucket URL (where PRANA packets are stored)
            karma_tracker_url: Karma Tracker API URL
            poll_interval: Seconds between polls
            batch_size: Number of packets to process per batch
        """
        self.bucket_url = bucket_url.rstrip('/')
        # If karma_tracker_url is not provided, use same base URL (integrated mode)
        if karma_tracker_url:
            self.karma_tracker_url = karma_tracker_url.rstrip('/')
        else:
            # Use same backend URL since Karma Tracker is now integrated
            self.karma_tracker_url = bucket_url.rstrip('/')
        self.poll_interval = poll_interval
        self.batch_size = batch_size
        self.running = False
    
    def determine_karma_action(self, packet: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Determine karma action based on PRANA packet data.
        
        Maps cognitive states and focus scores to karma actions.
        
        Returns:
            Dict with action, intensity, and note, or None if no action
        """
        cognitive_state = packet.get("cognitive_state", "").upper()
        focus_score = packet.get("focus_score", 0.0)
        active_seconds = packet.get("active_seconds", 0.0)
        
        # High focus + active = positive karma
        if cognitive_state in ["ON_TASK", "DEEP_FOCUS"] and focus_score >= 70:
            if active_seconds >= 4.0:  # Mostly active
                return {
                    "action": "completing_lessons",
                    "intensity": min(1.0, focus_score / 100.0),
                    "note": f"Focused learning: {cognitive_state}, focus={focus_score:.1f}"
                }
        
        # Low focus or distracted = negative karma (use cheat action for now)
        # Note: Karma Tracker doesn't have a "distracted" action, so we use "cheat" for severe cases
        # For minor distractions, we might skip karma change to avoid false penalties
        elif cognitive_state in ["DISTRACTED", "OFF_TASK"]:
            if active_seconds < 1.0 and focus_score < 30:  # Very distracted
                return {
                    "action": "cheat",  # Using cheat as penalty for severe distraction
                    "intensity": 0.5,  # Reduced intensity since it's not actual cheating
                    "note": f"Severely distracted: {cognitive_state}, focus={focus_score:.1f}, active={active_seconds:.1f}s"
                }
        
        # Away = no karma change (neutral)
        elif cognitive_state == "AWAY":
            return None  # No karma change for being away
        
        # Default: neutral for other states
        return None
    
    def process_packet(self, packet: Dict[str, Any]) -> Dict[str, Any]:
        """
        Process a single packet and update karma.
        
        Returns:
            Dict with processing result
        """
        packet_id = packet.get("packet_id")
        user_id = packet.get("user_id")
        
        if not user_id or user_id == "unknown" or user_id == "null":
            logger.debug(f"Skipping packet {packet_id}: no user_id (user not logged in) - will mark as processed")
            return {"success": False, "reason": "invalid_user_id"}
        
        # Determine karma action
        karma_action = self.determine_karma_action(packet)
        
        if not karma_action:
            # No karma change needed, but mark as processed
            logger.debug(f"Packet {packet_id}: No karma action needed")
            return {"success": True, "action": None}
        
        try:
            # Call Karma Tracker API
            response = requests.post(
                f"{self.karma_tracker_url}/api/v1/karma/log-action/",
                json={
                    "user_id": user_id,
                    "action": karma_action["action"],
                    "intensity": karma_action.get("intensity", 1.0),
                    "role": "learner",
                    "note": karma_action.get("note", ""),
                    "context": f"prana-bucket: cognitive_state={packet.get('cognitive_state')}"
                },
                timeout=10
            )
            
            if response.status_code == 200:
                karma_result = response.json()
                logger.info(f"Packet {packet_id}: Karma updated - {karma_action['action']}")
                return {
                    "success": True,
                    "action": karma_action["action"],
                    "karma_result": karma_result
                }
            else:
                logger.error(f"Packet {packet_id}: Karma API error - {response.status_code}")
                return {"success": False, "reason": f"karma_api_error_{response.status_code}"}
                
        except requests.RequestException as e:
            logger.error(f"Packet {packet_id}: Failed to call Karma Tracker - {e}")
            return {"success": False, "reason": "karma_api_failed"}
    
    def mark_packet_processed(
        self,
        packet_id: str,
        success: bool,
        karma_actions: Optional[List[Dict[str, Any]]] = None
    ) -> bool:
        """Mark a packet as processed in the bucket"""
        try:
            response = requests.post(
                f"{self.bucket_url}/api/v1/bucket/prana/packets/mark-processed",
                json={
                    "packet_id": packet_id,
                    "success": success,
                    "karma_actions": karma_actions or []
                },
                timeout=5
            )
            return response.status_code == 200
        except Exception as e:
            logger.error(f"Failed to mark packet {packet_id} as processed: {e}")
            return False
    
    def poll_and_process(self) -> Dict[str, Any]:
        """
        Poll bucket for pending packets and process them.
        
        Returns:
            Dict with processing statistics
        """
        try:
            # Get pending packets
            response = requests.get(
                f"{self.bucket_url}/api/v1/bucket/prana/packets/pending",
                params={"limit": self.batch_size},
                timeout=10
            )
            
            if response.status_code != 200:
                logger.error(f"Failed to get pending packets: {response.status_code}")
                return {"processed": 0, "errors": 1}
            
            data = response.json()
            packets = data.get("packets", [])
            
            if not packets:
                return {"processed": 0, "queue_size": data.get("queue_size", 0)}
            
            logger.info(f"Processing {len(packets)} packets...")
            
            processed = 0
            errors = 0
            karma_actions = []
            
            for packet in packets:
                packet_id = packet.get("packet_id")
                
                # Process packet
                result = self.process_packet(packet)
                
                if result.get("success"):
                    processed += 1
                    if result.get("action"):
                        karma_actions.append({
                            "action": result["action"],
                            "packet_id": packet_id
                        })
                else:
                    errors += 1
                    # Log reason for failure (but still mark as processed)
                    reason = result.get("reason", "unknown")
                    if reason == "invalid_user_id":
                        logger.debug(f"Packet {packet_id}: Skipped (no user_id) - marking as processed")
                
                # Mark as processed (even if karma update failed, to avoid reprocessing)
                # Format karma_actions as list of dicts (backend expects this format)
                karma_actions_list = None
                if result.get("action"):
                    karma_actions_list = [{
                        "action": result["action"],
                        "packet_id": packet_id,
                        "intensity": result.get("karma_result", {}).get("intensity", 1.0) if result.get("karma_result") else 1.0
                    }]
                
                self.mark_packet_processed(
                    packet_id,
                    success=result.get("success", False),
                    karma_actions=karma_actions_list
                )
            
            return {
                "processed": processed,
                "errors": errors,
                "total": len(packets),
                "queue_size": data.get("queue_size", 0),
                "karma_actions": len(karma_actions)
            }
            
        except requests.RequestException as e:
            logger.error(f"Failed to poll bucket: {e}")
            return {"processed": 0, "errors": 1, "error": str(e)}
    
    def start_consumer(self):
        """Start continuous polling loop"""
        self.running = True
        logger.info(f"Starting bucket consumer (poll every {self.poll_interval}s)")
        
        while self.running:
            try:
                stats = self.poll_and_process()
                
                if stats.get("processed", 0) > 0:
                    logger.info(
                        f"Processed {stats['processed']}/{stats.get('total', 0)} packets. "
                        f"Queue: {stats.get('queue_size', 0)} remaining"
                    )
                
                time.sleep(self.poll_interval)
                
            except KeyboardInterrupt:
                logger.info("Consumer stopped by user")
                self.running = False
                break
            except Exception as e:
                logger.error(f"Consumer error: {e}")
                time.sleep(self.poll_interval)
    
    def stop_consumer(self):
        """Stop the consumer"""
        self.running = False
        logger.info("Stopping bucket consumer")


# Convenience function for quick testing
def process_pending_packets(
    bucket_url: str = "http://localhost:3000",
    karma_tracker_url: str = None,  # None = integrated mode (uses bucket_url)
    limit: int = 10
) -> Dict[str, Any]:
    """
    Process a batch of pending packets (one-time call).
    
    Useful for testing or manual processing.
    """
    consumer = BucketConsumer(
        bucket_url=bucket_url,
        karma_tracker_url=karma_tracker_url,  # None = integrated mode
        batch_size=limit
    )
    return consumer.poll_and_process()


if __name__ == "__main__":
    # Run consumer (integrated mode - uses same URL for bucket and karma)
    import os
    
    bucket_url = os.getenv("BUCKET_API_BASE_URL", "http://localhost:3000")
    # In integrated mode, karma uses same URL as bucket
    karma_url = os.getenv("KARMA_TRACKER_API_BASE_URL", None)  # None = use bucket_url
    
    poll_interval = int(os.getenv("POLL_INTERVAL_SECONDS", "5"))
    batch_size = int(os.getenv("BATCH_SIZE", "10"))
    
    consumer = BucketConsumer(
        bucket_url=bucket_url,
        karma_tracker_url=karma_url,  # None = integrated mode
        poll_interval=poll_interval,
        batch_size=batch_size
    )
    
    print(f"Starting Bucket Consumer (Integrated Mode)...")
    print(f"Backend URL: {bucket_url} (bucket + karma endpoints)")
    print(f"Poll Interval: {poll_interval}s")
    print(f"Batch Size: {batch_size}")
    print(f"Press Ctrl+C to stop")
    
    try:
        consumer.start_consumer()
    except KeyboardInterrupt:
        consumer.stop_consumer()

