"""
Append-Only Storage Service for BHIV Bucket
============================================

Core Philosophy:
- Bucket is MEMORY, not DECISION
- Artifacts are stored EXACTLY as produced
- NO modification, NO deletion, NO interpretation
- Tamper-evident through hash chains
- Deterministic replay guaranteed

Architecture:
- Append-only log (JSONL format)
- Each artifact is independent
- Hash chain for integrity
- Server-computed hashes (never trust client)
- Domain-agnostic validation

Reference: APPEND_LOG_STORAGE.md
"""

import json
import hashlib
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from utils.logger import get_logger

logger = get_logger(__name__)


class AppendOnlyStorage:
    """
    Append-only artifact storage with tamper-evident hash chains.
    
    Key Guarantees:
    1. Immutability - artifacts never modified after write
    2. Deterministic hashing - server computes all hashes
    3. Chain integrity - each artifact links to parent
    4. Replayability - deterministic ordering guaranteed
    5. Domain neutrality - no payload interpretation
    """
    
    # Configuration
    MAX_PAYLOAD_SIZE = 16 * 1024 * 1024  # 16MB (configurable)
    REQUIRED_METADATA_FIELDS = [
        "artifact_id",
        "trace_id",
        "timestamp_utc",
        "schema_version",
        "source_module_id",
        "artifact_type"
    ]
    ALLOWED_ENVELOPE_FIELDS = [
        "artifact_id",
        "trace_id",
        "timestamp_utc",
        "schema_version",
        "source_module_id",
        "artifact_type",
        "parent_hash",
        "payload",
        "hash"
    ]
    CURRENT_SCHEMA_VERSION = "1.0.0"
    
    def __init__(self, storage_path: str = None):
        """
        Initialize append-only storage.
        
        Args:
            storage_path: Directory for artifact storage. If None, will use
                the `BHIV_ARTIFACT_PATH` environment variable or default to
                `data/artifacts`.
        """
        # Allow overriding storage path via environment variable for staging
        if storage_path is None:
            storage_path = os.getenv("BHIV_ARTIFACT_PATH", "data/artifacts")
        self.storage_path = Path(storage_path)
        self.storage_path.mkdir(parents=True, exist_ok=True)
        
        # Append-only log file (JSONL format)
        self.log_file = self.storage_path / "artifact_log.jsonl"
        
        # Index for fast lookups (artifact_id -> file position)
        self.index_file = self.storage_path / "artifact_index.json"
        
        # Chain state (last artifact hash)
        self.chain_state_file = self.storage_path / "chain_state.json"
        
        # Initialize storage
        self._initialize_storage()
        
        logger.info(f"Append-only storage initialized at {self.storage_path}")
    
    def _initialize_storage(self):
        """Initialize storage files if they don't exist."""
        # Create log file if it doesn't exist
        if not self.log_file.exists():
            self.log_file.touch()
            logger.info("Created new artifact log file")
        
        # Create index if it doesn't exist
        if not self.index_file.exists():
            self._save_index({})
            logger.info("Created new artifact index")
        
        # Create chain state if it doesn't exist
        if not self.chain_state_file.exists():
            self._save_chain_state({"last_hash": None, "artifact_count": 0})
            logger.info("Created new chain state")
    
    def _load_index(self) -> Dict[str, int]:
        """Load artifact index from disk."""
        try:
            with open(self.index_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load index: {e}")
            return {}
    
    def _save_index(self, index: Dict[str, int]):
        """Save artifact index to disk."""
        try:
            with open(self.index_file, 'w') as f:
                json.dump(index, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save index: {e}")
    
    def _load_chain_state(self) -> Dict:
        """Load chain state from disk."""
        try:
            with open(self.chain_state_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            logger.error(f"Failed to load chain state: {e}")
            return {"last_hash": None, "artifact_count": 0}
    
    def _save_chain_state(self, state: Dict):
        """Save chain state to disk."""
        try:
            with open(self.chain_state_file, 'w') as f:
                json.dump(state, f, indent=2)
        except Exception as e:
            logger.error(f"Failed to save chain state: {e}")
    
    def compute_hash(self, artifact: Dict) -> str:
        """
        Compute deterministic SHA256 hash of artifact.
        
        CRITICAL: Server computes hash, never trust client.
        
        Hash includes:
        - artifact_id
        - timestamp_utc
        - schema_version
        - source_module_id
        - artifact_type
        - parent_hash (if present)
        - payload (serialized deterministically)
        
        Args:
            artifact: Artifact dictionary
            
        Returns:
            SHA256 hash as hex string
        """
        # Create deterministic representation
        hash_input = {
            "artifact_id": artifact.get("artifact_id"),
            "trace_id": artifact.get("trace_id"),
            "timestamp_utc": artifact.get("timestamp_utc"),
            "schema_version": artifact.get("schema_version"),
            "source_module_id": artifact.get("source_module_id"),
            "artifact_type": artifact.get("artifact_type"),
            "parent_hash": artifact.get("parent_hash"),
            "payload": artifact.get("payload")
        }
        
        # Serialize deterministically (sorted keys, no whitespace)
        serialized = json.dumps(hash_input, sort_keys=True, separators=(',', ':'))
        
        # Compute SHA256
        hash_bytes = hashlib.sha256(serialized.encode('utf-8')).hexdigest()
        
        return hash_bytes

    def _extract_artifact_payload(self, entry: Dict) -> Dict:
        """Return the client artifact payload exactly as stored."""
        if isinstance(entry, dict) and "artifact" in entry and isinstance(entry["artifact"], dict):
            return entry["artifact"]
        return entry
    
    def validate_artifact_structure(self, artifact: Dict) -> Tuple[bool, Optional[str]]:
        """
        Validate artifact structure (NOT payload content).
        
        Validates:
        1. Required metadata fields present
        2. No unknown envelope fields
        3. Schema version valid
        4. Payload size within limits
        5. Parent hash exists (if not first artifact)
        
        Does NOT validate:
        - Payload content (domain-agnostic)
        - Business logic
        - Data meaning
        
        Args:
            artifact: Artifact to validate
            
        Returns:
            (is_valid, error_message)
        """
        # 1. Check required metadata fields
        for field in self.REQUIRED_METADATA_FIELDS:
            if field not in artifact:
                return False, f"Missing required field: {field}"
        
        # 2. Check for unknown envelope fields
        for field in artifact.keys():
            if field not in self.ALLOWED_ENVELOPE_FIELDS:
                return False, f"Unknown envelope field: {field}. Schema drift detected."
        
        # 3. Validate schema version
        schema_version = artifact.get("schema_version")
        if schema_version != self.CURRENT_SCHEMA_VERSION:
            return False, f"Invalid schema version: {schema_version}. Expected: {self.CURRENT_SCHEMA_VERSION}"
        
        # 4. Validate payload size
        payload = artifact.get("payload")
        if payload:
            payload_size = len(json.dumps(payload).encode('utf-8'))
            if payload_size > self.MAX_PAYLOAD_SIZE:
                return False, f"Payload size {payload_size} exceeds limit {self.MAX_PAYLOAD_SIZE}"
        
        # 5. Validate parent hash (if not first artifact)
        chain_state = self._load_chain_state()
        if chain_state["artifact_count"] > 0:
            # Not the first artifact, must have parent_hash
            if "parent_hash" not in artifact:
                return False, "parent_hash required (not first artifact)"
            
            parent_hash = artifact.get("parent_hash")
            if parent_hash != chain_state["last_hash"]:
                return False, f"Invalid parent_hash. Expected: {chain_state['last_hash']}, Got: {parent_hash}"
        else:
            # First artifact, must NOT have parent_hash
            if "parent_hash" in artifact and artifact["parent_hash"] is not None:
                return False, "First artifact must not have parent_hash"
        
        return True, None
    
    def store_artifact(self, artifact: Dict) -> Dict:
        """
        Store artifact in append-only log.
        
        Process:
        1. Validate structure (NOT content)
        2. Check for duplicate artifact_id
        3. Compute server-side hash
        4. Append to log (atomic write)
        5. Update index
        6. Update chain state
        
        Args:
            artifact: Artifact to store (without hash)
            
        Returns:
            Stored artifact with computed hash
            
        Raises:
            ValueError: If validation fails
        """
        # 1. Validate structure
        is_valid, error = self.validate_artifact_structure(artifact)
        if not is_valid:
            logger.error(f"Artifact validation failed: {error}")
            raise ValueError(f"Artifact validation failed: {error}")
        
        # 2. Check for duplicate artifact_id
        index = self._load_index()
        artifact_id = artifact["artifact_id"]
        if artifact_id in index:
            logger.error(f"Duplicate artifact_id: {artifact_id}")
            raise ValueError(f"Duplicate artifact_id: {artifact_id}")
        
        # 3. Compute server-side hash (NEVER trust client)
        artifact_copy = json.loads(json.dumps(artifact))
        computed_hash = self.compute_hash(artifact_copy)
        record = {
            "artifact": artifact_copy,
            "hash": computed_hash,
        }
        
        # 4. Append to log (atomic write)
        try:
            with open(self.log_file, 'a') as f:
                # Get current position before write
                position = f.tell()
                
                # Write wrapper record as single line (JSONL format)
                f.write(json.dumps(record, separators=(',', ':')) + '\n')
                f.flush()
                os.fsync(f.fileno())  # Force write to disk
                
                logger.info(f"Artifact {artifact_id} appended at position {position}")
        except Exception as e:
            logger.error(f"Failed to append artifact: {e}")
            raise ValueError(f"Failed to append artifact: {e}")
        
        # 5. Update index
        index[artifact_id] = position
        self._save_index(index)
        
        # 6. Update chain state
        chain_state = self._load_chain_state()
        chain_state["last_hash"] = computed_hash
        chain_state["artifact_count"] += 1
        self._save_chain_state(chain_state)
        
        logger.info(f"Artifact {artifact_id} stored successfully with hash {computed_hash}")

        return {
            "artifact": artifact_copy,
            "hash": computed_hash,
            "artifact_id": artifact_id,
            "parent_hash": artifact_copy.get("parent_hash"),
            "timestamp_utc": artifact_copy.get("timestamp_utc"),
        }
    
    def get_artifact(self, artifact_id: str) -> Optional[Dict]:
        """
        Retrieve artifact by ID.
        
        Args:
            artifact_id: Artifact ID to retrieve
            
        Returns:
            Artifact dictionary or None if not found
        """
        index = self._load_index()
        
        if artifact_id not in index:
            logger.warning(f"Artifact not found: {artifact_id}")
            return None
        
        position = index[artifact_id]
        
        try:
            with open(self.log_file, 'r') as f:
                f.seek(position)
                line = f.readline()
                entry = json.loads(line)
                return self._extract_artifact_payload(entry)
        except Exception as e:
            logger.error(f"Failed to read artifact {artifact_id}: {e}")
            return None

    def get_artifacts_by_trace_id(self, trace_id: str) -> List[Dict]:
        """Return all stored artifacts for a trace_id, preserving payload exactly."""
        matches: List[Dict] = []

        try:
            with open(self.log_file, 'r') as f:
                for line in f:
                    if not line.strip():
                        continue
                    entry = json.loads(line)
                    artifact = self._extract_artifact_payload(entry)
                    if artifact.get("trace_id") == trace_id:
                        matches.append(artifact)
        except Exception as e:
            logger.error(f"Failed to query artifacts by trace_id {trace_id}: {e}")

        return matches
    
    def list_artifacts(self, limit: int = 100, offset: int = 0) -> Dict:
        """
        List artifacts in chronological order.
        
        Args:
            limit: Maximum number of artifacts to return
            offset: Number of artifacts to skip
            
        Returns:
            Dictionary with artifacts list and metadata
        """
        artifacts = []
        
        try:
            with open(self.log_file, 'r') as f:
                # Skip offset lines
                for _ in range(offset):
                    f.readline()
                
                # Read limit lines
                for _ in range(limit):
                    line = f.readline()
                    if not line:
                        break
                    entry = json.loads(line)
                    artifacts.append(self._extract_artifact_payload(entry))
        except Exception as e:
            logger.error(f"Failed to list artifacts: {e}")
        
        chain_state = self._load_chain_state()
        
        return {
            "artifacts": artifacts,
            "count": len(artifacts),
            "total": chain_state["artifact_count"],
            "offset": offset,
            "limit": limit
        }
    
    def validate_chain_integrity(self) -> Tuple[bool, List[str]]:
        """
        Validate entire artifact chain integrity.
        
        Checks:
        1. Each artifact hash is correct
        2. Parent hash chain is valid
        3. No orphan artifacts
        4. Deterministic ordering
        
        Returns:
            (is_valid, list_of_errors)
        """
        errors = []
        previous_hash = None
        artifact_count = 0
        
        try:
            with open(self.log_file, 'r') as f:
                for line_num, line in enumerate(f, 1):
                    if not line.strip():
                        continue
                    
                    try:
                        entry = json.loads(line)
                        artifact = self._extract_artifact_payload(entry)
                        artifact_count += 1
                        
                        # Verify hash
                        stored_hash = entry.get("hash")
                        computed_hash = self.compute_hash(artifact)
                        
                        if stored_hash != computed_hash:
                            errors.append(
                                f"Line {line_num}: Hash mismatch for {artifact.get('artifact_id')}. "
                                f"Stored: {stored_hash}, Computed: {computed_hash}"
                            )
                        
                        # Verify parent chain
                        if artifact_count == 1:
                            # First artifact should not have parent
                            if artifact.get("parent_hash") is not None:
                                errors.append(f"Line {line_num}: First artifact has parent_hash")
                        else:
                            # Subsequent artifacts must link to previous
                            if artifact.get("parent_hash") != previous_hash:
                                errors.append(
                                    f"Line {line_num}: Parent hash mismatch. "
                                    f"Expected: {previous_hash}, Got: {artifact.get('parent_hash')}"
                                )
                        
                        previous_hash = stored_hash
                        
                    except json.JSONDecodeError as e:
                        errors.append(f"Line {line_num}: Invalid JSON - {e}")
        
        except Exception as e:
            errors.append(f"Failed to read log file: {e}")
        
        is_valid = len(errors) == 0
        
        if is_valid:
            logger.info(f"Chain integrity validated: {artifact_count} artifacts")
        else:
            logger.error(f"Chain integrity validation failed: {len(errors)} errors")
        
        return is_valid, errors
    
    def get_chain_state(self) -> Dict:
        """Get current chain state."""
        return self._load_chain_state()
    
    def get_storage_stats(self) -> Dict:
        """Get storage statistics."""
        chain_state = self._load_chain_state()
        
        log_size = 0
        if self.log_file.exists():
            log_size = self.log_file.stat().st_size
        
        return {
            "artifact_count": chain_state["artifact_count"],
            "last_hash": chain_state["last_hash"],
            "log_file_size_bytes": log_size,
            "log_file_size_mb": round(log_size / (1024 * 1024), 2),
            "storage_path": str(self.storage_path),
            "schema_version": self.CURRENT_SCHEMA_VERSION,
            "max_payload_size_mb": self.MAX_PAYLOAD_SIZE / (1024 * 1024)
        }


# Global storage instance
# The storage path can be overridden with the BHIV_ARTIFACT_PATH env var
append_only_storage = AppendOnlyStorage()
