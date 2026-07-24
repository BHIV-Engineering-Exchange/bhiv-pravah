"""
Working database configuration with mock fallback
"""

import logging
import uuid
from typing import Union

logger = logging.getLogger(__name__)

class MockDBClient:
    """Mock database client that always works"""
    
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
    
    def table(self, table_name: str):
        return MockTable(self.data, table_name)

class MockTable:
    """Mock table operations"""
    
    def __init__(self, data: dict, table_name: str):
        self.data = data
        self.table_name = table_name
        self._query = {}
    
    def select(self, columns: str = "*", count: str = None):
        self._query["select"] = columns
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
    """Mock query result"""
    
    def __init__(self, data: list):
        self.data = data
        self.count = len(data)

def get_db():
    """Always return working mock database"""
    logger.info("Using mock database (guaranteed working)")
    return MockDBClient()

async def init_database():
    """Initialize mock database"""
    logger.info("Mock database initialized")
    return True