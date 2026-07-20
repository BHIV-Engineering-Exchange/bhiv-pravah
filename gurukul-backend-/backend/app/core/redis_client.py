"""
Redis Client for Bucket Queue

Handles Redis connection and queue operations for PRANA packets.
Falls back gracefully if Redis is not available.
"""

import os
import json
import logging
from typing import Optional, List, Dict, Any
from datetime import datetime, timedelta

logger = logging.getLogger(__name__)

# Try to import redis, but handle gracefully if not installed
try:
    import redis
    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning("Redis not installed. Queue features will be disabled. Install with: pip install redis")


class RedisQueue:
    """Redis-based queue for PRANA packets"""
    
    def __init__(self):
        self.client = None
        self.is_connected = False
        
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available. Using in-memory fallback.")
            self._in_memory_queue = []
            return
        
        try:
            redis_host = os.getenv("REDIS_HOST", "localhost")
            redis_port = int(os.getenv("REDIS_PORT", 6379))
            redis_password = os.getenv("REDIS_PASSWORD", None)
            redis_username = os.getenv("REDIS_USERNAME", None)
            
            redis_config = {
                "host": redis_host,
                "port": redis_port,
                "decode_responses": True,
                "socket_timeout": 5,
                "socket_connect_timeout": 5,
                "retry_on_timeout": True
            }
            
            if redis_password:
                redis_config["password"] = redis_password
            if redis_username:
                redis_config["username"] = redis_username
            
            self.client = redis.Redis(**redis_config)
            self.client.ping()
            self.is_connected = True
            logger.info(f"Connected to Redis at {redis_host}:{redis_port}")
        except Exception as e:
            logger.warning(f"Redis connection failed: {e}. Using in-memory fallback.")
            self._in_memory_queue = []
    
    def enqueue_packet(self, packet_id: str, packet_data: Dict[str, Any]) -> bool:
        """Add a packet to the queue"""
        try:
            if self.is_connected and self.client:
                # Add to queue list
                self.client.lpush("prana_packets:queue", packet_id)
                # Store packet data
                self.client.setex(
                    f"prana_packet:{packet_id}",
                    86400 * 7,  # 7 days TTL
                    json.dumps(packet_data)
                )
                return True
            else:
                # In-memory fallback
                self._in_memory_queue.append({"packet_id": packet_id, "data": packet_data})
                return True
        except Exception as e:
            logger.error(f"Failed to enqueue packet: {e}")
            return False
    
    def dequeue_packets(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get pending packets from queue"""
        try:
            if self.is_connected and self.client:
                packets = []
                for _ in range(limit):
                    packet_id = self.client.rpop("prana_packets:queue")
                    if not packet_id:
                        break
                    
                    packet_data = self.client.get(f"prana_packet:{packet_id}")
                    if packet_data:
                        packets.append({
                            "packet_id": packet_id,
                            "data": json.loads(packet_data)
                        })
                return packets
            else:
                # In-memory fallback
                result = self._in_memory_queue[:limit]
                self._in_memory_queue = self._in_memory_queue[limit:]
                return result
        except Exception as e:
            logger.error(f"Failed to dequeue packets: {e}")
            return []
    
    def get_queue_size(self) -> int:
        """Get number of packets in queue"""
        try:
            if self.is_connected and self.client:
                return self.client.llen("prana_packets:queue")
            else:
                return len(self._in_memory_queue)
        except Exception as e:
            logger.error(f"Failed to get queue size: {e}")
            return 0
    
    def remove_packet(self, packet_id: str) -> bool:
        """Remove a packet from storage (after processing)"""
        try:
            if self.is_connected and self.client:
                self.client.delete(f"prana_packet:{packet_id}")
                return True
            else:
                # In-memory fallback - already removed in dequeue
                return True
        except Exception as e:
            logger.error(f"Failed to remove packet: {e}")
            return False


# Global instance
_redis_queue = None

def get_redis_queue() -> RedisQueue:
    """Get or create Redis queue instance"""
    global _redis_queue
    if _redis_queue is None:
        _redis_queue = RedisQueue()
    return _redis_queue

