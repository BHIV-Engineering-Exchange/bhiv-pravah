#!/usr/bin/env python3
"""
Bucket Production Validation — Write/read proof, provenance tracking, integrity verification.
Validates that application artifacts are written through the platform layer and can be read back.
"""

import os
import time
import uuid
import json
import hashlib
import logging
from typing import Dict, Any, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)

SCHEMA_VERSION = os.getenv("PLATFORM_SCHEMA_VERSION", "1.0.0")

# ─── Bucket Validation Router ──────────────────────────────────────────

bucket_validation_router = APIRouter(prefix="/bucket-validation", tags=["Bucket Production Validation"])

@bucket_validation_router.post("/write-and-verify")
async def write_and_verify(request: Request):
    """
    Write an artifact to bucket, read it back, verify integrity.
    Produces write proof and read proof with content hash comparison.
    """
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    execution_id = getattr(request.state, "execution_id", str(uuid.uuid4()))
    start_time = time.time()

    try:
        from core import bhiv_bucket

        # Generate test artifact
        test_content = {
            "artifact_id": f"validation_{int(time.time())}",
            "trace_id": trace_id,
            "execution_id": execution_id,
            "content": "Bucket production validation test artifact",
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "schema_version": SCHEMA_VERSION
        }

        content_str = json.dumps(test_content, default=str, ensure_ascii=False, indent=2)
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()
        artifact_id = test_content["artifact_id"]
        filename = f"{artifact_id}.json"

        # ─── Write Phase ───
        write_start = time.time()
        try:
            write_path = bhiv_bucket.save_json("logs", filename, test_content)
            write_duration_ms = (time.time() - write_start) * 1000
            write_success = True
        except Exception as e:
            write_duration_ms = (time.time() - write_start) * 1000
            write_success = False
            write_path = None
            return JSONResponse(
                status_code=500,
                content={
                    "trace_id": trace_id,
                    "schema_version": SCHEMA_VERSION,
                    "status": "error",
                    "module": "bucket_validation",
                    "execution_id": execution_id,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                    "duration_ms": round((time.time() - start_time) * 1000, 2),
                    "error": {"code": "WRITE_FAILED", "message": f"Bucket write failed: {e}"}
                }
            )

        # ─── Read Phase ───
        read_start = time.time()
        try:
            read_path = bhiv_bucket.get_bucket_path("logs", filename)
            with open(read_path, "r", encoding="utf-8") as f:
                read_content = json.load(f)
            read_duration_ms = (time.time() - read_start) * 1000
            read_success = True
        except Exception as e:
            read_duration_ms = (time.time() - read_start) * 1000
            read_success = False
            read_content = None

        # ─── Verify Phase ───
        if read_success and read_content:
            read_str = json.dumps(read_content, default=str, ensure_ascii=False, indent=2)
            read_hash = hashlib.sha256(read_str.encode("utf-8")).hexdigest()
            integrity_match = read_hash == content_hash
        else:
            read_hash = None
            integrity_match = False

        # ─── Provenance ───
        provenance = {
            "artifact_id": artifact_id,
            "trace_id": trace_id,
            "execution_id": execution_id,
            "module": "bucket_validation",
            "artifact_type": "validation_test",
            "content_hash": content_hash,
            "read_hash": read_hash,
            "integrity_verified": integrity_match,
            "storage_path": write_path,
            "read_path": read_path,
            "write_timestamp": datetime.now(timezone.utc).isoformat(),
            "provenance_chain": [
                {"step": "write", "status": "success", "duration_ms": round(write_duration_ms, 2), "path": write_path},
                {"step": "read", "status": "success" if read_success else "failed", "duration_ms": round(read_duration_ms, 2)},
                {"step": "verify", "status": "match" if integrity_match else "mismatch", "write_hash": content_hash, "read_hash": read_hash}
            ]
        }

        # Persist provenance record
        try:
            provenance_filename = f"provenance_{artifact_id}.json"
            bhiv_bucket.save_json("logs", provenance_filename, provenance)
        except Exception:
            pass

        duration_ms = (time.time() - start_time) * 1000

        return {
            "trace_id": trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": "success" if integrity_match else "error",
            "module": "bucket_validation",
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": round(duration_ms, 2),
            "data": {
                "write_proof": {
                    "success": write_success,
                    "path": write_path,
                    "duration_ms": round(write_duration_ms, 2),
                    "content_hash": content_hash,
                    "file_size_bytes": len(content_str)
                },
                "read_proof": {
                    "success": read_success,
                    "path": read_path,
                    "duration_ms": round(read_duration_ms, 2),
                    "content_hash": read_hash
                },
                "integrity": {
                    "verified": integrity_match,
                    "write_hash": content_hash,
                    "read_hash": read_hash
                },
                "provenance": provenance
            }
        }

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        logger.error(f"Bucket validation failed: {e}")
        return JSONResponse(
            status_code=500,
            content={
                "trace_id": trace_id,
                "schema_version": SCHEMA_VERSION,
                "status": "error",
                "module": "bucket_validation",
                "execution_id": execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": round(duration_ms, 2),
                "error": {"code": "VALIDATION_FAILED", "message": str(e)}
            }
        )

@bucket_validation_router.get("/status")
async def bucket_status(request: Request):
    """Get bucket storage status and configuration."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    execution_id = getattr(request.state, "execution_id", str(uuid.uuid4()))

    try:
        from core import bhiv_bucket
        stats = bhiv_bucket.get_storage_stats()

        return {
            "trace_id": trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": "success",
            "module": "bucket_validation",
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0,
            "data": stats
        }
    except Exception as e:
        return {
            "trace_id": trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": "error",
            "module": "bucket_validation",
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0,
            "error": {"code": "STATUS_FAILED", "message": str(e)}
        }

@bucket_validation_router.get("/list-artifacts")
async def list_artifacts(segment: str = "logs", limit: int = 20, request: Request = None):
    """List recent artifacts in a bucket segment."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4())) if request else str(uuid.uuid4())
    execution_id = getattr(request.state, "execution_id", str(uuid.uuid4())) if request else str(uuid.uuid4())

    try:
        from core import bhiv_bucket
        files = bhiv_bucket.list_bucket_files(segment)

        return {
            "trace_id": trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": "success",
            "module": "bucket_validation",
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0,
            "data": {
                "segment": segment,
                "files": files[:limit],
                "total_files": len(files)
            }
        }
    except Exception as e:
        return {
            "trace_id": trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": "error",
            "module": "bucket_validation",
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0,
            "error": {"code": "LIST_FAILED", "message": str(e)}
        }

@bucket_validation_router.get("/read-artifact/{artifact_id}")
async def read_artifact(artifact_id: str, request: Request):
    """Read a specific artifact by ID and verify its integrity."""
    trace_id = getattr(request.state, "trace_id", str(uuid.uuid4()))
    execution_id = getattr(request.state, "execution_id", str(uuid.uuid4()))

    try:
        from core import bhiv_bucket

        filename = f"{artifact_id}.json"
        file_path = bhiv_bucket.get_bucket_path("logs", filename)

        with open(file_path, "r", encoding="utf-8") as f:
            content = json.load(f)

        content_str = json.dumps(content, default=str, ensure_ascii=False, indent=2)
        content_hash = hashlib.sha256(content_str.encode("utf-8")).hexdigest()

        # Check if provenance record exists
        provenance_filename = f"provenance_{artifact_id}.json"
        provenance = None
        try:
            prov_path = bhiv_bucket.get_bucket_path("logs", provenance_filename)
            with open(prov_path, "r", encoding="utf-8") as f:
                provenance = json.load(f)
        except Exception:
            pass

        # Verify integrity against provenance if available
        integrity_verified = True
        if provenance and "content_hash" in provenance:
            integrity_verified = content_hash == provenance["content_hash"]

        return {
            "trace_id": trace_id,
            "schema_version": SCHEMA_VERSION,
            "status": "success",
            "module": "bucket_validation",
            "execution_id": execution_id,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "duration_ms": 0,
            "data": {
                "artifact_id": artifact_id,
                "content": content,
                "content_hash": content_hash,
                "integrity_verified": integrity_verified,
                "provenance": provenance,
                "file_size_bytes": len(content_str)
            }
        }

    except FileNotFoundError:
        return JSONResponse(
            status_code=404,
            content={
                "trace_id": trace_id,
                "schema_version": SCHEMA_VERSION,
                "status": "error",
                "module": "bucket_validation",
                "execution_id": execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": 0,
                "error": {"code": "ARTIFACT_NOT_FOUND", "message": f"Artifact '{artifact_id}' not found"}
            }
        )
    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={
                "trace_id": trace_id,
                "schema_version": SCHEMA_VERSION,
                "status": "error",
                "module": "bucket_validation",
                "execution_id": execution_id,
                "timestamp": datetime.now(timezone.utc).isoformat(),
                "duration_ms": 0,
                "error": {"code": "READ_FAILED", "message": str(e)}
            }
        )
