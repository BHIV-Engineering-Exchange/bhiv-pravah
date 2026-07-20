from typing import Any, Dict, List, Optional

from database.mongodb_connection import COLLECTIONS, get_async_db

TRACE_LINEAGE_COLLECTION = COLLECTIONS.get("setu_trace_lineage", "setu_trace_lineage")
TRACE_LOG_COLLECTION = COLLECTIONS.get("setu_trace_logs", "setu_trace_logs")
TELEMETRY_COLLECTION = COLLECTIONS.get("setu_telemetry_events", "setu_telemetry_events")
LINEAGE_COLLECTION = COLLECTIONS.get("setu_lineage_events", "setu_lineage_events")
SIGNAL_INGESTION_COLLECTION = COLLECTIONS.get("setu_signal_ingestion", "setu_signal_ingestion")
VISIBILITY_COLLECTION = COLLECTIONS.get("setu_visibility_records", "setu_visibility_records")


class MongoSetuStore:
    def __init__(self, db=None):
        self.db = db or get_async_db()

    def _collection(self, name: str):
        return self.db[name]

    def _serialize(self, doc: Optional[Dict[str, Any]]):
        if not doc:
            return None
        result = dict(doc)
        if "_id" in result:
            result["_id"] = str(result["_id"])
        return result

    async def get_trace_record(self, execution_id: str) -> Optional[Dict[str, Any]]:
        return await self._collection(TRACE_LINEAGE_COLLECTION).find_one({"execution_id": execution_id})

    async def get_trace_by_trace_id(self, trace_id: str) -> Optional[Dict[str, Any]]:
        return await self._collection(TRACE_LINEAGE_COLLECTION).find_one({"trace_id": trace_id})

    async def upsert_trace_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        await self._collection(TRACE_LINEAGE_COLLECTION).update_one(
            {"execution_id": record["execution_id"]},
            {"$setOnInsert": record},
            upsert=True
        )
        return record

    async def append_trace_log(self, log: Dict[str, Any]) -> Dict[str, Any]:
        await self._collection(TRACE_LOG_COLLECTION).insert_one(log)
        return log

    async def append_telemetry(self, event: Dict[str, Any]) -> Dict[str, Any]:
        await self._collection(TELEMETRY_COLLECTION).insert_one(event)
        return event

    async def append_lineage_event(self, event: Dict[str, Any]) -> Dict[str, Any]:
        await self._collection(LINEAGE_COLLECTION).insert_one(event)
        return event

    async def next_lineage_sequence(self, trace_id: str) -> int:
        count = await self._collection(LINEAGE_COLLECTION).count_documents({"trace_id": trace_id})
        return count + 1

    async def list_lineage_events(self, trace_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        cursor = self._collection(LINEAGE_COLLECTION).find({"trace_id": trace_id}).sort("sequence", 1).limit(limit)
        return [self._serialize(doc) async for doc in cursor]

    async def list_telemetry_events(self, trace_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        cursor = self._collection(TELEMETRY_COLLECTION).find({"trace_id": trace_id}).sort("timestamp", 1).limit(limit)
        return [self._serialize(doc) async for doc in cursor]

    async def list_trace_logs(self, trace_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        cursor = self._collection(TRACE_LOG_COLLECTION).find({"trace_id": trace_id}).sort("timestamp", 1).limit(limit)
        return [self._serialize(doc) async for doc in cursor]

    async def append_signal_ingestion(self, signal: Dict[str, Any]) -> Dict[str, Any]:
        await self._collection(SIGNAL_INGESTION_COLLECTION).insert_one(signal)
        return signal

    async def list_signal_ingestion(self, trace_id: str, limit: int = 200) -> List[Dict[str, Any]]:
        cursor = self._collection(SIGNAL_INGESTION_COLLECTION).find({"trace_id": trace_id}).sort("ingested_at", 1).limit(limit)
        return [self._serialize(doc) async for doc in cursor]

    async def append_visibility_record(self, record: Dict[str, Any]) -> Dict[str, Any]:
        await self._collection(VISIBILITY_COLLECTION).insert_one(record)
        return record

    async def list_visibility_records(self, trace_id: str, record_type: Optional[str] = None, filters: Optional[Dict[str, Any]] = None, limit: int = 200) -> List[Dict[str, Any]]:
        query = {"trace_id": trace_id}
        if record_type:
            query["record_type"] = record_type
        if filters:
            query.update(filters)
            
        cursor = self._collection(VISIBILITY_COLLECTION).find(query).sort("consumed_at", 1).limit(limit)
        return [self._serialize(doc) async for doc in cursor]
