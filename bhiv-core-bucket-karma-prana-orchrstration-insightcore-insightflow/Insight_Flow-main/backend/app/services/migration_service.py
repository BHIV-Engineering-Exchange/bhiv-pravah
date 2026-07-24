"""
Migration Service for API v1 to v2 transition
Handles compatibility, deprecation warnings, and migration tracking
"""

import logging
from typing import Dict, List, Optional
from datetime import datetime, timedelta
from app.core.database import get_db
import json

logger = logging.getLogger(__name__)


class MigrationService:
    """Service for managing API migration from v1 to v2"""
    
    def __init__(self):
        self.deprecation_date = datetime.utcnow() + timedelta(days=30)
        self.removal_date = datetime.utcnow() + timedelta(days=60)
    
    async def track_api_usage(self, user_id: str, api_version: str, endpoint: str):
        """Track API version usage for migration analytics"""
        try:
            db = get_db()
            
            usage_record = {
                "user_id": user_id,
                "api_version": api_version,
                "endpoint": endpoint,
                "timestamp": datetime.utcnow().isoformat(),
                "date": datetime.utcnow().date().isoformat()
            }
            
            # Store in migration_usage table (create if needed)
            db.table("migration_usage").insert(usage_record).execute()
            
        except Exception as e:
            logger.warning(f"Failed to track API usage: {e}")
    
    async def get_migration_status(self, user_id: str) -> Dict:
        """Get migration status for a specific user"""
        try:
            db = get_db()
            
            # Get usage statistics for last 30 days
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            usage_data = db.table("migration_usage").select("*").eq(
                "user_id", user_id
            ).gte("timestamp", thirty_days_ago).execute()
            
            v1_usage = len([u for u in usage_data.data if u["api_version"] == "v1"])
            v2_usage = len([u for u in usage_data.data if u["api_version"] == "v2"])
            total_usage = v1_usage + v2_usage
            
            migration_percentage = (v2_usage / total_usage * 100) if total_usage > 0 else 0
            
            return {
                "user_id": user_id,
                "migration_percentage": round(migration_percentage, 2),
                "v1_requests": v1_usage,
                "v2_requests": v2_usage,
                "total_requests": total_usage,
                "deprecation_date": self.deprecation_date.isoformat(),
                "removal_date": self.removal_date.isoformat(),
                "days_until_removal": (self.removal_date - datetime.utcnow()).days,
                "migration_recommended": migration_percentage < 50
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration status: {e}")
            return {
                "user_id": user_id,
                "migration_percentage": 0,
                "error": "Unable to retrieve migration status"
            }
    
    async def get_migration_analytics(self) -> Dict:
        """Get overall migration analytics for admin dashboard"""
        try:
            db = get_db()
            
            # Get usage data for last 30 days
            thirty_days_ago = (datetime.utcnow() - timedelta(days=30)).isoformat()
            
            usage_data = db.table("migration_usage").select("*").gte(
                "timestamp", thirty_days_ago
            ).execute()
            
            # Calculate statistics
            total_requests = len(usage_data.data)
            v1_requests = len([u for u in usage_data.data if u["api_version"] == "v1"])
            v2_requests = len([u for u in usage_data.data if u["api_version"] == "v2"])
            
            # Get unique users
            unique_users = len(set(u["user_id"] for u in usage_data.data))
            v1_users = len(set(u["user_id"] for u in usage_data.data if u["api_version"] == "v1"))
            v2_users = len(set(u["user_id"] for u in usage_data.data if u["api_version"] == "v2"))
            
            # Calculate daily usage trends
            daily_usage = {}
            for record in usage_data.data:
                date = record["date"]
                if date not in daily_usage:
                    daily_usage[date] = {"v1": 0, "v2": 0}
                daily_usage[date][record["api_version"]] += 1
            
            return {
                "total_requests": total_requests,
                "v1_requests": v1_requests,
                "v2_requests": v2_requests,
                "v2_adoption_percentage": round((v2_requests / total_requests * 100) if total_requests > 0 else 0, 2),
                "unique_users": unique_users,
                "v1_users": v1_users,
                "v2_users": v2_users,
                "user_migration_percentage": round((v2_users / unique_users * 100) if unique_users > 0 else 0, 2),
                "daily_usage": daily_usage,
                "deprecation_date": self.deprecation_date.isoformat(),
                "removal_date": self.removal_date.isoformat(),
                "days_until_removal": (self.removal_date - datetime.utcnow()).days
            }
            
        except Exception as e:
            logger.error(f"Failed to get migration analytics: {e}")
            return {"error": "Unable to retrieve migration analytics"}
    
    def get_deprecation_warnings(self, api_version: str) -> List[str]:
        """Get deprecation warnings for API version"""
        warnings = []
        
        if api_version == "v1":
            days_until_removal = (self.removal_date - datetime.utcnow()).days
            
            warnings.append(
                f"API v1 is deprecated and will be removed in {days_until_removal} days. "
                f"Please migrate to API v2. See /docs/migration for details."
            )
            
            if days_until_removal <= 7:
                warnings.append(
                    "URGENT: API v1 removal is imminent. Immediate migration to v2 required."
                )
        
        return warnings
    
    async def convert_v1_to_v2_request(self, v1_request: Dict) -> Dict:
        """Convert v1 request format to v2 format"""
        try:
            v2_request = {
                "input_data": v1_request.get("input_data", {}),
                "input_type": v1_request.get("input_type", "text"),
                "strategy": v1_request.get("strategy", "q_learning"),
                "context": v1_request.get("context", {}),
                "preferences": {}  # New in v2
            }
            
            # Add migration metadata
            v2_request["context"]["migrated_from_v1"] = True
            v2_request["context"]["migration_timestamp"] = datetime.utcnow().isoformat()
            
            return v2_request
            
        except Exception as e:
            logger.error(f"Failed to convert v1 to v2 request: {e}")
            raise ValueError(f"Request conversion failed: {e}")
    
    async def convert_v2_to_v1_response(self, v2_response: Dict) -> Dict:
        """Convert v2 response format to v1 format for backward compatibility"""
        try:
            # Extract core v1 fields from enhanced v2 response
            routing_decision = v2_response.get("routing_decision", {})
            
            v1_response = {
                "request_id": v2_response.get("metadata", {}).get("request_id"),
                "routing_log_id": routing_decision.get("routing_log_id"),
                "agent_id": routing_decision.get("agent_id"),
                "agent_name": routing_decision.get("agent_name"),
                "agent_type": routing_decision.get("agent_type"),
                "confidence_score": routing_decision.get("confidence_score"),
                "routing_reason": routing_decision.get("routing_reason"),
                "routing_strategy": v2_response.get("metadata", {}).get("strategy_used")
            }
            
            return v1_response
            
        except Exception as e:
            logger.error(f"Failed to convert v2 to v1 response: {e}")
            raise ValueError(f"Response conversion failed: {e}")
    
    async def create_migration_table(self):
        """Create migration tracking table if it doesn't exist"""
        try:
            db = get_db()
            
            # Check if table exists by trying to query it
            try:
                db.table("migration_usage").select("*").limit(1).execute()
                logger.info("Migration usage table already exists")
            except:
                # Table doesn't exist, create it via SQL
                logger.info("Creating migration usage table")
                # Note: This would need to be done via Supabase SQL editor
                # as the Python client doesn't support DDL operations
                pass
                
        except Exception as e:
            logger.warning(f"Could not verify/create migration table: {e}")


# Global migration service instance
migration_service = MigrationService()