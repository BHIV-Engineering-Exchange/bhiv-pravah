#!/usr/bin/env python3
"""
Database Adapter - Provides unified interface for both SQLite and MongoDB
Automatically selects the appropriate database based on environment configuration
"""

import os
from dotenv import load_dotenv

load_dotenv()

# Determine which database to use
DATABASE_TYPE = os.getenv('DATABASE_TYPE', 'mongodb').lower()

if DATABASE_TYPE == 'mongodb':
    print("[INFO] Using MongoDB database")
    from database.mongodb_service import MongoDBService as DatabaseService
    from database.mongodb_crm_service import MongoDBCRMService as CRMService
    from database.mongodb_connection import MongoDBConnection
    
    def init_database():
        """Initialize MongoDB database"""
        from database.mongodb_connection import get_db
        from database.mongodb_models import create_indexes
        
        # Test connection
        if not MongoDBConnection.test_connection():
            raise Exception("Failed to connect to MongoDB")
        
        # Get database and create indexes
        db = get_db()
        create_indexes(db)
        print("[OK] MongoDB initialized successfully")
        return db
    
    def get_database():
        """Get MongoDB database instance"""
        return MongoDBConnection.get_database()

else:
    print("[INFO] Using SQLite database")
    from database.service import DatabaseService
    from database.crm_service import CRMService
    from database.models import init_database, SessionLocal
    
    def get_database():
        """Get SQLite database session"""
        return SessionLocal()


# Export unified interface
__all__ = ['DatabaseService', 'CRMService', 'init_database', 'get_database', 'DATABASE_TYPE']
