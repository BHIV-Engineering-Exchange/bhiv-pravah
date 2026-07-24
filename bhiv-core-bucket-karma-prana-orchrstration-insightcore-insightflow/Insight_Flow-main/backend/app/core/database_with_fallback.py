from supabase import create_client, Client
from app.core.config import settings
from typing import Optional, Union
import logging
import uuid

logger = logging.getLogger(__name__)


class MockDBClient:
    """Mock database client for when Supabase is unavailable"""
    
    def __init__(self):
        self.data = {
            "agents": [
                {"id": "nlp-001", "name": "NLP Processor", "type": "nlp", "status": "active", "performance_score": 0.85, "success_rate": 0.90},
                {"id": "tts-001", "name": "TTS Generator", "type": "tts", "status": "active", "performance_score": 0.80, "success_rate": 0.85},
                {"id": "cv-001", "name": "Vision Analyzer", "type": "computer_vision", "status": "active", "performance_score": 0.75, "success_rate": 0.80}
            ],
            "routing_logs": [],
            "feedback_events": []
        }
        logger.info("Mock database initialized with sample data")
    
    def table(self, table_name: str):
        return MockTable(self.data, table_name)


class MockTable:
    """Mock table for database operations"""
    
    def __init__(self, data: dict, table_name: str):
        self.data = data
        self.table_name = table_name
        self._query = {}
    
    def select(self, columns: str = "*", count: str = None):
        self._query["select"] = columns
        if count:
            self._query["count"] = count
        return self
    
    def eq(self, column: str, value):
        self._query["where"] = {column: value}
        return self
    
    def limit(self, count: int):
        self._query["limit"] = count
        return self
    
    def insert(self, data: dict):
        if self.table_name not in self.data:
            self.data[self.table_name] = []
        
        if "id" not in data:
            data["id"] = str(uuid.uuid4())
        
        self.data[self.table_name].append(data)
        return MockResult([data])
    
    def update(self, data: dict):
        return MockResult([])
    
    def execute(self):
        table_data = self.data.get(self.table_name, [])
        
        if "where" in self._query:
            where_clause = self._query["where"]
            filtered_data = [item for item in table_data 
                           if all(item.get(k) == v for k, v in where_clause.items())]
        else:
            filtered_data = table_data
        
        if "limit" in self._query:
            filtered_data = filtered_data[:self._query["limit"]]
        
        return MockResult(filtered_data)


class MockResult:
    """Mock result for database queries"""
    
    def __init__(self, data: list):
        self.data = data
        self.count = len(data)


class SupabaseClient:
    """Singleton Supabase client manager with fallback"""
    
    _instance: Optional[Union[Client, MockDBClient]] = None
    _use_mock = False
    
    @classmethod
    def get_client(cls) -> Union[Client, MockDBClient]:
        """Get or create database client instance with fallback"""
        if cls._instance is None:
            try:
                if not settings.SUPABASE_URL or not settings.SUPABASE_SERVICE_KEY:
                    raise ValueError("Supabase credentials not configured")
                
                # Try Supabase connection
                client = create_client(
                    supabase_url=settings.SUPABASE_URL,
                    supabase_key=settings.SUPABASE_SERVICE_KEY
                )
                
                # Test connection
                client.table("agents").select("*").limit(1).execute()
                
                cls._instance = client
                cls._use_mock = False
                logger.info("Supabase client initialized successfully")
                
            except Exception as e:
                logger.warning(f"Supabase connection failed: {e}")
                logger.info("Falling back to mock database")
                cls._instance = MockDBClient()
                cls._use_mock = True
        
        return cls._instance
    
    @classmethod
    def is_using_mock(cls) -> bool:
        """Check if using mock database"""
        return cls._use_mock


def get_db() -> Union[Client, MockDBClient]:
    """Dependency for getting database client"""
    return SupabaseClient.get_client()


def is_mock_db() -> bool:
    """Check if currently using mock database"""
    return SupabaseClient.is_using_mock()


async def init_database():
    """Initialize database tables and indexes"""
    try:
        db = get_db()
        
        if is_mock_db():
            logger.info("Mock database ready for development")
        else:
            # Verify Supabase tables
            tables_to_check = ["agents", "routing_logs", "feedback_events"]
            
            for table in tables_to_check:
                try:
                    result = db.table(table).select("*", count="exact").limit(1).execute()
                    logger.info(f"Table '{table}' verified - {result.count} records")
                except Exception as e:
                    logger.warning(f"Table '{table}' issue: {e}")
            
            logger.info("Supabase database connected and verified")
            
    except Exception as e:
        logger.warning(f"Database initialization warning: {e}")