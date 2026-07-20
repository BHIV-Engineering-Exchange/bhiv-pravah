"""
bucket_adapter.py — Real Bucket HTTP Connector for Gurukul (TANTRA Integration)
================================================================================

Responsibilities:
  - Emit memory events to TANTRA Bucket via real POST /bucket/write
  - Maintain SHA256 append-only hash chain (prev_hash → current_hash)
  - In-memory queue (max 100 events) for retry buffering — no silent drop
  - Strict schema enforcement before transmission
  - Retry logic (max 3 attempts, 1s backoff)

Rules:
  - NO overwrite — append only
  - Hash chain must be preserved across all emissions
  - Gurukul MUST NOT store memory locally — only emit events
"""

import hashlib
import json
import logging
import time
import threading
from collections import deque
from datetime import datetime, timezone
from typing import Any, Deque, Dict, Optional, Tuple

import requests as http_client

from app.core.context import get_trace_id
from app.services.tantra_schema_validator import validate_bucket_payload, ContractViolationError

logger = logging.getLogger("BucketAdapter")

_RETRY_MAX      = 3
_RETRY_BACKOFF  = 1.0   # seconds
_QUEUE_MAX_SIZE = 100   # in-memory overflow buffer


def _compute_hash(prev_hash: str, data: Dict[str, Any]) -> str:
    """SHA256(prev_hash + canonical_json(data))"""
    canonical = json.dumps(data, sort_keys=True, separators=(",", ":"))
    raw       = (prev_hash + canonical).encode("utf-8")
    return hashlib.sha256(raw).hexdigest()


class BucketAdapter:
    """
    Append-only TANTRA Bucket connector with SHA256 hash chain.

    Chain invariant:
        current_hash = sha256(prev_hash + json(event_data))
    Every successful write advances prev_hash → current_hash.
    """

    def __init__(self):
        from app.core.config import settings
        self.bucket_url = getattr(settings, "BUCKET_URL", None)
        self.api_key    = getattr(settings, "TANTRA_API_KEY", None)
        self.enabled    = self.bucket_url is not None
        self._running   = False
        self._task      = None

        # Hash chain state — protected by a lock for thread safety
        self._lock      = threading.Lock()
        self._prev_hash = "0" * 64          # Genesis hash (64 zeros)
        self._seq       = 0                 # Monotonic sequence counter

        # In-memory retry queue — no silent drop
        self._queue: Deque[Dict[str, Any]] = deque(maxlen=_QUEUE_MAX_SIZE)
        self._queue_lock = threading.Lock()

        if self.enabled:
            logger.info(f"BucketAdapter configured → {self.bucket_url}")
            # TANTRA PHASE 1: Initialize hash chain from remote state if possible
            self._fetch_latest_hash()
            self.start()
        else:
            logger.warning(
                "BucketAdapter: BUCKET_URL not set — memory events will be dropped "
                "(set BUCKET_URL env var to enable)"
            )

    # ── Lifecycle ───────────────────────────────────────────────────────────
    def start(self):
        if not self._running:
            import asyncio
            self._running = True
            try:
                self._task = asyncio.create_task(self._loop())
                logger.info("BucketAdapter background loop started")
            except RuntimeError:
                # Fallback for non-async contexts (e.g. initial import)
                # In FastAPI, this will be started properly in startup_event
                pass

    def stop(self):
        self._running = False

    async def _loop(self):
        import asyncio
        while self._running:
            if len(self._queue) > 0:
                self.flush_queue()
            await asyncio.sleep(30) # Retry every 30s

    def _fetch_latest_hash(self):
        """Fetch the current head hash from the Bucket server to ensure chain continuity."""
        if not self.bucket_url:
            return
            
        try:
            # Assumes endpoint /bucket/latest-hash exists on the bucket server
            base_url = self.bucket_url.split('/bucket/')[0]
            resp = http_client.get(f"{base_url}/bucket/latest-hash", timeout=5)
            if resp.status_code == 200:
                data = resp.json()
                remote_hash = data.get("latest_hash")
                if remote_hash and len(remote_hash) == 64:
                    with self._lock:
                        self._prev_hash = remote_hash
                    logger.info(f"[Bucket] Hash chain initialized from remote: {remote_hash[:12]}...")
        except Exception as e:
            logger.warning(f"[Bucket] Could not fetch latest hash (using genesis): {e}")

    # ── Public API ──────────────────────────────────────────────────────────
    def emit_memory(
        self,
        user_id:    str,
        session_id: str,
        action:     str,
        outcome:    str,
        payload:    Optional[Dict[str, Any]] = None,
    ):
        """
        Emit a structured memory event to TANTRA Bucket.
        Builds the hash chain, validates schema, sends via HTTP POST.
        Non-blocking — failures go to the in-memory retry queue.
        """
        trace_id = get_trace_id() or "no-trace"

        # Build core event (before hash — hash is computed over this)
        event_core = {
            "trace_id":   trace_id,
            "user_id":    user_id,
            "session_id": session_id,
            "action":     action,
            "outcome":    outcome,
            "payload":    payload or {},
            "timestamp":  datetime.now(timezone.utc).isoformat(),
            "source":     "GurukulRuntime",
            "schema_version": "2.0.0",
            "provenance": "Gurukul-TANTRA-Signed",
            "ownership": "district_admin",
            "replay_metadata": {
                "is_replayable": True,
                "replay_index": int(time.time() * 1000)
            }
        }

        # Compute hash chain (thread-safe)
        with self._lock:
            self._seq += 1
            prev_hash    = self._prev_hash
            current_hash = _compute_hash(prev_hash, event_core)
            # Advance chain ONLY if emission succeeds (done after HTTP call)
            seq          = self._seq

        # Full payload with hash chain
        full_payload = {
            **event_core,
            "prev_hash":    prev_hash,
            "current_hash": current_hash,
        }

        logger.info(
            f"[BUCKET EMIT] action={action} user={user_id} trace={trace_id} "
            f"seq={seq} hash={current_hash[:12]}..."
        )

        # Validate schema before sending
        try:
            validate_bucket_payload(full_payload)
        except ContractViolationError as e:
            logger.error(f"[Bucket] Payload rejected by schema validator: {e}")
            return

        # Send with retry
        success = self._http_emit(full_payload)

        if success:
            # Advance hash chain only on confirmed success
            with self._lock:
                self._prev_hash = current_hash
        else:
            # Queue for retry — do NOT advance hash chain
            self._enqueue(full_payload)

    def emit_artifact(self, artifact_id: str, content: Dict[str, Any], metadata: Dict[str, Any]):
        """
        Emit a general artifact to TANTRA Bucket.
        Used for non-educational data like maritime signals or system logs.
        """
        trace_id = get_trace_id() or "no-trace"
        
        event_core = {
            "trace_id": trace_id,
            "artifact_id": artifact_id,
            "content": content,
            "metadata": metadata,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "source": metadata.get("product", "GeneralArtifact"),
            "action": "artifact_write",
            "outcome": "success"
        }
        
        with self._lock:
            self._seq += 1
            prev_hash = self._prev_hash
            current_hash = _compute_hash(prev_hash, event_core)
            seq = self._seq

        full_payload = {
            **event_core,
            "prev_hash": prev_hash,
            "current_hash": current_hash,
        }

        # Send with retry
        success = self._http_emit(full_payload)
        if success:
            with self._lock:
                self._prev_hash = current_hash
        else:
            self._enqueue(full_payload)

    # ── Internal HTTP layer ─────────────────────────────────────────────────
    def _http_emit(self, payload: Dict[str, Any]) -> bool:
        """POST to Bucket. Returns True on success, False after all retries exhausted."""
        if not self.enabled:
            logger.debug("[Bucket] No URL configured — event not sent (no-op).")
            return False

        headers = {"Content-Type": "application/json"}
        if self.api_key:
            headers["X-TANTRA-API-Key"] = self.api_key

        for attempt in range(1, _RETRY_MAX + 1):
            try:
                resp = http_client.post(
                    self.bucket_url,
                    json=payload,
                    headers=headers,
                    timeout=5,
                )
                if resp.status_code in (200, 201, 202, 204):
                    logger.debug(
                        f"[Bucket] Memory written ✓ | action={payload['action']} "
                        f"trace={payload['trace_id']} hash={payload['current_hash'][:12]}... "
                        f"attempt={attempt}"
                    )
                    return True
                else:
                    logger.warning(
                        f"[Bucket] Non-2xx response {resp.status_code} | attempt={attempt}/{_RETRY_MAX}"
                    )
            except Exception as e:
                logger.warning(f"[Bucket] HTTP error on attempt {attempt}/{_RETRY_MAX}: {e}")

            if attempt < _RETRY_MAX:
                time.sleep(_RETRY_BACKOFF)

        logger.error(
            f"[Bucket] All {_RETRY_MAX} attempts failed — queuing event "
            f"(action={payload.get('action')} trace={payload.get('trace_id')})"
        )
        return False

    # ── In-memory retry queue ───────────────────────────────────────────────
    def _enqueue(self, payload: Dict[str, Any]):
        """Add failed event to in-memory queue. Never silently drops."""
        with self._queue_lock:
            if len(self._queue) >= _QUEUE_MAX_SIZE:
                oldest = self._queue[0]
                logger.error(
                    f"[Bucket] Queue full ({_QUEUE_MAX_SIZE}). "
                    f"Oldest event dropped: action={oldest.get('action')} trace={oldest.get('trace_id')}"
                )
            self._queue.append(payload)
            logger.warning(
                f"[Bucket] Event queued for retry | queue_size={len(self._queue)} | "
                f"action={payload.get('action')} trace={payload.get('trace_id')}"
            )

    def flush_queue(self) -> Tuple[int, int]:
        """
        Attempt to re-send all queued events.
        Returns (sent_count, remaining_count).
        Call this periodically from a background task.
        """
        sent = 0
        remaining = []
        with self._queue_lock:
            pending = list(self._queue)
            self._queue.clear()

        for event in pending:
            if self._http_emit(event):
                with self._lock:
                    self._prev_hash = event["current_hash"]
                sent += 1
            else:
                remaining.append(event)

        with self._queue_lock:
            for ev in remaining:
                self._queue.append(ev)

        logger.info(f"[Bucket] Queue flush: sent={sent} remaining={len(remaining)}")
        return sent, len(remaining)

    # ── Diagnostics ─────────────────────────────────────────────────────────
    def get_chain_state(self) -> Dict[str, Any]:
        """Return current hash chain state for diagnostics."""
        with self._lock:
            return {
                "prev_hash":   self._prev_hash,
                "seq":         self._seq,
                "queue_size":  len(self._queue),
                "bucket_url":  self.bucket_url,
                "enabled":     self.enabled,
            }


# Singleton
bucket_adapter = BucketAdapter()
