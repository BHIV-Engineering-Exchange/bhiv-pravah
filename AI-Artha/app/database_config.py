"""Database configuration - MongoDB backend"""

import os
from .config import MONGO_URI, MONGO_DB_NAME


def get_database_url():
    """Get MongoDB connection URI"""
    return MONGO_URI


def get_database_name():
    """Get MongoDB database name"""
    return MONGO_DB_NAME
