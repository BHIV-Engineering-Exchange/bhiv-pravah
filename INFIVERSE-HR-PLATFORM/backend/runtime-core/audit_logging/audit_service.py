"""
Audit Logging Service for Sovereign Application Runtime (SAR)

This module provides comprehensive audit logging with provenance tracking
for all operations in multi-tenant applications.
"""
import json
import uuid
from datetime import datetime, timezone
from enum import Enum
from typing import Dict, Any, Optional, List
from dataclasses import dataclass, asdict
from abc import ABC, abstractmethod
import os
import threading
import queue
import time
from concurrent.futures import ThreadPoolExecutor
import logging
from auth.auth_service import sar_auth
from tenancy.tenant_service import sar_tenant_resolver
from role_enforcement.rbac_service import sar_rbac
from pymongo import MongoClient
import os
import logging

logger = logging.getLogger(__name__)


class AuditEventType(Enum):
    """Enumeration of audit event types"""
    USER_LOGIN = "user_login"
    USER_LOGOUT = "user_logout"
    USER_REGISTER = "user_register"
    API_ACCESS = "api_access"
    DATA_ACCESS = "data_access"
    DATA_MODIFICATION = "data_modification"
    ROLE_ASSIGNMENT = "role_assignment"
    PERMISSION_CHANGE = "permission_change"
    TENANT_ACCESS = "tenant_access"
    TENANT_CREATION = "tenant_creation"
    SECURITY_EVENT = "security_event"
    CONFIG_CHANGE = "config_change"
    FILE_UPLOAD = "file_upload"
    FILE_DOWNLOAD = "file_download"
    SYSTEM_ERROR = "system_error"


@dataclass
class AuditEvent:
    """Represents an audit event with all necessary provenance information"""
    event_id: str
    event_type: AuditEventType
    timestamp: datetime
    user_id: Optional[str]
    tenant_id: Optional[str]
    client_ip: Optional[str]
    user_agent: Optional[str]
    resource: str
    action: str
    resource_id: Optional[str]
    old_values: Optional[Dict[str, Any]] = None
    new_values: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    session_id: Optional[str] = None
    correlation_id: Optional[str] = None
    success: bool = True
    error_message: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert the audit event to a dictionary for serialization"""
        result = asdict(self)
        result['event_type'] = self.event_type.value
        result['timestamp'] = self.timestamp.isoformat()
        return result

    def to_json(self) -> str:
        """Convert the audit event to JSON string"""
        return json.dumps(self.to_dict())


class AuditStorageBackend(ABC):
    """Abstract base class for audit storage backends"""
    
    @abstractmethod
    def store_event(self, event: AuditEvent) -> bool:
        """Store an audit event"""
        pass

    @abstractmethod
    def get_events(self, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Retrieve audit events with optional filters"""
        pass

    @abstractmethod
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve a specific audit event by ID"""
        pass


class InMemoryAuditStorage(AuditStorageBackend):
    """In-memory audit storage for development/testing purposes"""
    
    def __init__(self):
        self._events: List[AuditEvent] = []
        self._lock = threading.Lock()
    
    def store_event(self, event: AuditEvent) -> bool:
        with self._lock:
            self._events.append(event)
            # Keep only the last 10000 events to prevent memory issues
            if len(self._events) > 10000:
                self._events = self._events[-10000:]
        return True
    
    def get_events(self, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        with self._lock:
            events = self._events[offset:offset + limit]
            
            if filters:
                filtered_events = []
                for event in events:
                    match = True
                    event_dict = event.to_dict()
                    
                    for key, value in filters.items():
                        if key not in event_dict or event_dict[key] != value:
                            match = False
                            break
                    
                    if match:
                        filtered_events.append(event)
                
                return filtered_events
            
            return events
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        with self._lock:
            for event in self._events:
                if event.event_id == event_id:
                    return event
            return None


class MongoAuditStorage(AuditStorageBackend):
    """MongoDB Atlas-based audit storage for persistent logging"""
    
    def __init__(self, mongodb_uri: str = None):
        self.mongodb_uri = mongodb_uri or os.getenv("MONGODB_URI", "mongodb://localhost:27017")
        self.db_name = os.getenv("MONGODB_DB_NAME", "bhiv_hr")
        self.collection_name = "audit_logs"
        self._client = None
        self._db = None
        self._collection = None
        self._connect()
    
    def _connect(self):
        """Establish MongoDB connection"""
        try:
            self._client = MongoClient(self.mongodb_uri)
            self._db = self._client[self.db_name]
            self._collection = self._db[self.collection_name]
            # Create index for efficient queries
            self._collection.create_index([("timestamp", -1)])
            self._collection.create_index([("user_id", 1)])
            self._collection.create_index([("tenant_id", 1)])
            self._collection.create_index([("event_type", 1)])
            logger.info(f"✅ Connected to MongoDB audit logs collection: {self.collection_name}")
        except Exception as e:
            logger.error(f"❌ Failed to connect to MongoDB for audit logs: {e}")
            self._client = None
            self._db = None
            self._collection = None
    
    def store_event(self, event: AuditEvent) -> bool:
        """Store audit event in MongoDB"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for audit logging")
            return False
        
        try:
            event_dict = event.to_dict()
            # Convert datetime to ISO format for MongoDB
            if isinstance(event_dict.get("timestamp"), datetime):
                event_dict["timestamp"] = event_dict["timestamp"].isoformat()
            
            result = self._collection.insert_one(event_dict)
            logger.debug(f"✅ Audit event stored: {event.event_id}")
            return True
        except Exception as e:
            logger.error(f"❌ Failed to store audit event: {e}")
            return False
    
    def get_events(self, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Retrieve audit events from MongoDB"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for audit logging")
            return []
        
        try:
            query = {}
            if filters:
                # Convert filters to MongoDB query format
                for key, value in filters.items():
                    if key == "start_date" and value:
                        query.setdefault("timestamp", {})["$gte"] = value
                    elif key == "end_date" and value:
                        query.setdefault("timestamp", {})["$lte"] = value
                    elif key not in ["start_date", "end_date"]:
                        query[key] = value
            
            # Sort by timestamp descending (newest first)
            cursor = self._collection.find(query).sort("timestamp", -1).skip(offset).limit(limit)
            events = []
            
            for doc in cursor:
                try:
                    event = AuditEvent.from_dict(doc)
                    events.append(event)
                except Exception as e:
                    logger.error(f"❌ Failed to parse audit event from MongoDB: {e}")
                    continue
            
            logger.debug(f"✅ Retrieved {len(events)} audit events from MongoDB")
            return events
        except Exception as e:
            logger.error(f"❌ Failed to retrieve audit events: {e}")
            return []
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve specific audit event by ID"""
        if not self._collection:
            logger.error("❌ MongoDB collection not available for audit logging")
            return None
        
        try:
            doc = self._collection.find_one({"event_id": event_id})
            if doc:
                return AuditEvent.from_dict(doc)
            return None
        except Exception as e:
            logger.error(f"❌ Failed to retrieve audit event by ID: {e}")
            return None


class FileAuditStorage(AuditStorageBackend):
    """File-based audit storage for persistent logging"""
    
    def __init__(self, log_directory: str = "audit_logs"):
        self.log_directory = log_directory
        os.makedirs(log_directory, exist_ok=True)
        self._lock = threading.Lock()
    
    def store_event(self, event: AuditEvent) -> bool:
        try:
            # Create daily log files
            date_str = event.timestamp.strftime("%Y-%m-%d")
            log_file = os.path.join(self.log_directory, f"audit_{date_str}.log")
            
            with self._lock:
                with open(log_file, 'a', encoding='utf-8') as f:
                    f.write(event.to_json() + '\n')
            
            return True
        except Exception as e:
            print(f"Error storing audit event: {e}")
            return False
    
    def get_events(self, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        # For file storage, this is a simplified implementation
        # In production, you'd want to use a more efficient search mechanism
        events = []
        # This is a basic implementation - in real usage, you'd need to read from files
        # and potentially use a database or other indexing solution
        return events[offset:offset + limit]
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        # This is a simplified implementation
        # In production, you'd need to implement efficient lookup
        return None


class AuditConfig:
    """Configuration for the audit logging service"""
    def __init__(self):
        self.enabled = os.getenv("AUDIT_LOGGING_ENABLED", "true").lower() == "true"
        self.storage_backend = os.getenv("AUDIT_STORAGE_BACKEND", "mongodb")  # mongodb, file, or memory
        self.log_level = os.getenv("AUDIT_LOG_LEVEL", "INFO")
        self.retention_days = int(os.getenv("AUDIT_RETENTION_DAYS", "90"))
        self.batch_size = int(os.getenv("AUDIT_BATCH_SIZE", "100"))
        self.flush_interval = int(os.getenv("AUDIT_FLUSH_INTERVAL", "5"))  # seconds
        self.log_sensitive_data = os.getenv("AUDIT_LOG_SENSITIVE_DATA", "false").lower() == "true"
        self.queue_size = int(os.getenv("AUDIT_QUEUE_SIZE", "1000"))
        self.async_writes = os.getenv("AUDIT_ASYNC_WRITES", "true").lower() == "true"


class SARAuditLogging:
    """Main audit logging service class for the Sovereign Application Runtime"""
    
    def __init__(self):
        self.config = AuditConfig()
        self._setup_storage_backend()
        self._setup_async_processing()
        self._event_queue = queue.Queue(maxsize=self.config.queue_size)
        self._stop_event = threading.Event()
        
        if self.config.async_writes:
            self._start_background_worker()
    
    def _setup_storage_backend(self):
        """Initialize the appropriate storage backend based on configuration"""
        if self.config.storage_backend == "memory":
            self.storage = InMemoryAuditStorage()
        elif self.config.storage_backend == "mongodb":
            mongodb_uri = os.getenv("MONGODB_URI")
            self.storage = MongoAuditStorage(mongodb_uri)
        else:
            log_dir = os.getenv("AUDIT_LOG_DIR", "audit_logs")
            self.storage = FileAuditStorage(log_dir)
    
    def _setup_async_processing(self):
        """Setup async processing if enabled"""
        if self.config.async_writes:
            self._executor = ThreadPoolExecutor(max_workers=1)
        else:
            self._executor = None
    
    def _start_background_worker(self):
        """Start background worker for processing audit events"""
        self._worker_thread = threading.Thread(target=self._process_events, daemon=True)
        self._worker_thread.start()
    
    def _process_events(self):
        """Background worker to process audit events from the queue"""
        batch = []
        last_flush = time.time()
        
        while not self._stop_event.is_set():
            try:
                # Wait for an event with timeout
                try:
                    event = self._event_queue.get(timeout=1)
                    batch.append(event)
                except queue.Empty:
                    # Continue to flush check
                    pass
                
                # Flush batch if it's full or timeout reached
                current_time = time.time()
                if (len(batch) >= self.config.batch_size or 
                    (current_time - last_flush) >= self.config.flush_interval):
                    if batch:
                        for e in batch:
                            self.storage.store_event(e)
                        batch = []
                        last_flush = current_time
            except Exception as e:
                print(f"Error in audit event processing: {e}")
        
        # Flush remaining events
        if batch:
            for e in batch:
                self.storage.store_event(e)
    
    def log_event(self, event_type: AuditEventType, user_id: Optional[str] = None,
                  tenant_id: Optional[str] = None, client_ip: Optional[str] = None,
                  user_agent: Optional[str] = None, resource: str = "",
                  action: str = "", resource_id: Optional[str] = None,
                  old_values: Optional[Dict[str, Any]] = None,
                  new_values: Optional[Dict[str, Any]] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  session_id: Optional[str] = None,
                  correlation_id: Optional[str] = None,
                  success: bool = True,
                  error_message: Optional[str] = None) -> bool:
        """Log an audit event with provenance tracking"""
        if not self.config.enabled:
            return True
        
        # Create a unique event ID
        event_id = str(uuid.uuid4())
        
        # Create audit event
        event = AuditEvent(
            event_id=event_id,
            event_type=event_type,
            timestamp=datetime.now(timezone.utc),
            user_id=user_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource=resource,
            action=action,
            resource_id=resource_id,
            old_values=old_values,
            new_values=new_values,
            metadata=metadata or {},
            session_id=session_id,
            correlation_id=correlation_id,
            success=success,
            error_message=error_message
        )
        
        if self.config.async_writes:
            try:
                self._event_queue.put(event, block=False)
                return True
            except queue.Full:
                # Queue is full, log synchronously as fallback
                return self.storage.store_event(event)
        else:
            return self.storage.store_event(event)
    
    def log_api_access(self, request, response_status: int = 200, 
                      user_id: Optional[str] = None, 
                      tenant_id: Optional[str] = None) -> bool:
        """Log API access events"""
        if not self.config.enabled:
            return True
        
        # Extract information from request
        client_ip = request.client.host if hasattr(request, 'client') else None
        user_agent = request.headers.get('user-agent')
        resource = request.url.path
        action = request.method
        correlation_id = request.headers.get('x-correlation-id') or str(uuid.uuid4())
        
        return self.log_event(
            event_type=AuditEventType.API_ACCESS,
            user_id=user_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource=resource,
            action=action,
            correlation_id=correlation_id,
            success=response_status < 400,
            metadata={
                "response_status": response_status,
                "content_length": response_status,  # This would be actual content length in real implementation
                "request_method": action,
                "request_path": resource
            }
        )
    
    def log_data_access(self, user_id: str, tenant_id: str, resource: str,
                       resource_id: str, success: bool = True) -> bool:
        """Log data access events"""
        if not self.config.enabled:
            return True
        
        return self.log_event(
            event_type=AuditEventType.DATA_ACCESS,
            user_id=user_id,
            tenant_id=tenant_id,
            resource=resource,
            action="read",
            resource_id=resource_id,
            success=success
        )
    
    def log_data_modification(self, user_id: str, tenant_id: str, resource: str,
                             resource_id: str, action: str, old_values: Optional[Dict[str, Any]] = None,
                             new_values: Optional[Dict[str, Any]] = None,
                             success: bool = True, error_message: Optional[str] = None) -> bool:
        """Log data modification events with old/new values for provenance tracking"""
        if not self.config.enabled:
            return True
        
        return self.log_event(
            event_type=AuditEventType.DATA_MODIFICATION,
            user_id=user_id,
            tenant_id=tenant_id,
            resource=resource,
            action=action,
            resource_id=resource_id,
            old_values=old_values if self.config.log_sensitive_data else None,
            new_values=new_values if self.config.log_sensitive_data else None,
            success=success,
            error_message=error_message
        )
    
    def log_user_login(self, user_id: str, client_ip: Optional[str] = None,
                      user_agent: Optional[str] = None, success: bool = True,
                      error_message: Optional[str] = None) -> bool:
        """Log user login events"""
        if not self.config.enabled:
            return True
        
        # Extract tenant information if available
        tenant_id = None  # Would come from authentication context in real usage
        
        return self.log_event(
            event_type=AuditEventType.USER_LOGIN,
            user_id=user_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            user_agent=user_agent,
            resource="user",
            action="login",
            success=success,
            error_message=error_message
        )
    
    def log_security_event(self, event_subtype: str, user_id: Optional[str] = None,
                          tenant_id: Optional[str] = None, client_ip: Optional[str] = None,
                          description: str = "", severity: str = "medium") -> bool:
        """Log security-related events"""
        if not self.config.enabled:
            return True
        
        return self.log_event(
            event_type=AuditEventType.SECURITY_EVENT,
            user_id=user_id,
            tenant_id=tenant_id,
            client_ip=client_ip,
            resource="security",
            action=event_subtype,
            success=False,  # Security events are typically concerning
            metadata={
                "description": description,
                "severity": severity,
                "event_subtype": event_subtype
            }
        )
    
    def get_events(self, filters: Optional[Dict[str, Any]] = None, 
                   limit: int = 100, offset: int = 0) -> List[AuditEvent]:
        """Retrieve audit events with optional filters"""
        return self.storage.get_events(filters, limit, offset)
    
    def get_event_by_id(self, event_id: str) -> Optional[AuditEvent]:
        """Retrieve a specific audit event by ID"""
        return self.storage.get_event_by_id(event_id)
    
    def shutdown(self):
        """Shutdown the audit logging service"""
        self._stop_event.set()
        if self._executor:
            self._executor.shutdown(wait=True)


# Global instance for the SAR Audit Logging service
sar_audit = SARAuditLogging()


def get_audit_trail(resource: str, resource_id: Optional[str] = None, 
                   tenant_id: Optional[str] = None, limit: int = 100) -> List[AuditEvent]:
    """Get the audit trail for a specific resource"""
    filters = {"resource": resource}
    if resource_id:
        filters["resource_id"] = resource_id
    if tenant_id:
        filters["tenant_id"] = tenant_id
    
    return sar_audit.get_events(filters=filters, limit=limit)


def log_user_activity(user_id: str, action: str, resource: str, 
                     resource_id: Optional[str] = None, 
                     tenant_id: Optional[str] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> bool:
    """Helper function to log user activity"""
    return sar_audit.log_event(
        event_type=AuditEventType.DATA_ACCESS,
        user_id=user_id,
        tenant_id=tenant_id,
        resource=resource,
        action=action,
        resource_id=resource_id,
        metadata=metadata
    )