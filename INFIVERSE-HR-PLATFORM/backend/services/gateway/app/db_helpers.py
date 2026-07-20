"""
MongoDB Helper Utilities for Gateway Service
Common functions for MongoDB operations with async/await support
"""
from bson import ObjectId
from typing import Optional, Dict, Any, List
from datetime import datetime, timezone
from motor.motor_asyncio import AsyncIOMotorDatabase, AsyncIOMotorCollection
from app.database import get_mongo_db


def convert_id_to_objectid(id_value: Any) -> ObjectId:
    """
    Convert integer ID or string to ObjectId
    
    Args:
        id_value: Integer ID, ObjectId, or string
        
    Returns:
        ObjectId
    """
    if isinstance(id_value, ObjectId):
        return id_value
    if isinstance(id_value, int):
        # For migration: we'll need to map integer IDs to ObjectIds
        # This is a placeholder - actual mapping will be done during data migration
        raise ValueError(f"Cannot convert integer ID {id_value} to ObjectId - use string ObjectId")
    if isinstance(id_value, str):
        if ObjectId.is_valid(id_value):
            return ObjectId(id_value)
        raise ValueError(f"Invalid ObjectId string: {id_value}")
    raise ValueError(f"Cannot convert {type(id_value)} to ObjectId")


def convert_objectid_to_str(doc: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convert _id ObjectId to string 'id' field for API responses
    
    Args:
        doc: MongoDB document with _id field
        
    Returns:
        Document with 'id' as string and _id removed
    """
    if doc and '_id' in doc:
        doc['id'] = str(doc['_id'])
        del doc['_id']
    return doc


async def find_one_by_field(
    collection_name: str,
    field: str,
    value: Any,
    projection: Optional[Dict[str, int]] = None
) -> Optional[Dict[str, Any]]:
    """
    Find one document by field value
    
    Args:
        collection_name: Name of the collection
        field: Field name to search
        value: Field value to match
        projection: Optional projection dictionary
        
    Returns:
        Document dict or None
    """
    db = await get_mongo_db()
    collection = db[collection_name]
    
    query = {field: value}
    doc = await collection.find_one(query, projection)
    
    if doc:
        return convert_objectid_to_str(doc)
    return None


async def find_many(
    collection_name: str,
    query: Optional[Dict[str, Any]] = None,
    limit: int = 50,
    offset: int = 0,
    sort: Optional[List[tuple]] = None,
    projection: Optional[Dict[str, int]] = None
) -> List[Dict[str, Any]]:
    """
    Find multiple documents with pagination
    
    Args:
        collection_name: Name of the collection
        query: MongoDB query dictionary
        limit: Maximum number of documents to return
        offset: Number of documents to skip
        sort: Sort specification as list of (field, direction) tuples
        projection: Optional projection dictionary
        
    Returns:
        List of documents
    """
    db = await get_mongo_db()
    collection = db[collection_name]
    
    cursor = collection.find(query or {}, projection)
    
    if sort:
        cursor = cursor.sort(sort)
    
    cursor = cursor.skip(offset).limit(limit)
    
    docs = await cursor.to_list(length=limit)
    return [convert_objectid_to_str(doc) for doc in docs]


async def count_documents(
    collection_name: str,
    query: Optional[Dict[str, Any]] = None
) -> int:
    """
    Count documents matching query
    
    Args:
        collection_name: Name of the collection
        query: MongoDB query dictionary
        
    Returns:
        Count of matching documents
    """
    db = await get_mongo_db()
    collection = db[collection_name]
    return await collection.count_documents(query or {})


async def insert_one(
    collection_name: str,
    document: Dict[str, Any]
) -> str:
    """
    Insert one document
    
    Args:
        collection_name: Name of the collection
        document: Document dictionary (should not include _id)
        
    Returns:
        Inserted document ID as string
    """
    db = await get_mongo_db()
    collection = db[collection_name]
    
    # Add timestamps if not present
    if 'created_at' not in document:
        document['created_at'] = datetime.now(timezone.utc)
    if 'updated_at' not in document:
        document['updated_at'] = datetime.now(timezone.utc)
    
    result = await collection.insert_one(document)
    return str(result.inserted_id)


async def update_one(
    collection_name: str,
    query: Dict[str, Any],
    update: Dict[str, Any],
    upsert: bool = False
) -> bool:
    """
    Update one document
    
    Args:
        collection_name: Name of the collection
        query: Query to find document
        update: Update dictionary (use $set, $unset, etc.)
        upsert: Create document if it doesn't exist
        
    Returns:
        True if document was updated
    """
    db = await get_mongo_db()
    collection = db[collection_name]
    
    # Add updated_at timestamp
    if '$set' in update:
        update['$set']['updated_at'] = datetime.now(timezone.utc)
    else:
        update = {'$set': {**update, 'updated_at': datetime.now(timezone.utc)}}
    
    result = await collection.update_one(query, update, upsert=upsert)
    return result.modified_count > 0 or result.upserted_id is not None


async def delete_one(
    collection_name: str,
    query: Dict[str, Any]
) -> bool:
    """
    Delete one document
    
    Args:
        collection_name: Name of the collection
        query: Query to find document
        
    Returns:
        True if document was deleted
    """
    db = await get_mongo_db()
    collection = db[collection_name]
    result = await collection.delete_one(query)
    return result.deleted_count > 0
