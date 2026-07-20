"""
Hash Generation Utilities
Provides deterministic hashing for replay validation and execution traceability
"""

import hashlib
import json
from typing import Dict, Any, List, Union
from dataclasses import dataclass

@dataclass
class HashResult:
    """Result of hash generation with metadata"""
    hash_value: str
    algorithm: str
    input_size: int
    normalized_input: str

class DeterministicHasher:
    """Generates deterministic hashes for replay validation"""
    
    def __init__(self, algorithm: str = "sha256"):
        self.algorithm = algorithm
        self.hash_func = getattr(hashlib, algorithm)
    
    def normalize_data(self, data: Any) -> str:
        """
        Normalize data for deterministic hashing
        
        Args:
            data: Data to normalize
            
        Returns:
            Normalized string representation
        """
        if isinstance(data, dict):
            # Sort keys recursively for deterministic ordering
            return json.dumps(self._sort_dict_recursive(data), separators=(',', ':'))
        elif isinstance(data, list):
            # Sort list items if they are comparable, otherwise preserve order
            try:
                sorted_data = sorted(data, key=lambda x: json.dumps(x, sort_keys=True))
                return json.dumps(sorted_data, separators=(',', ':'))
            except (TypeError, ValueError):
                # If items are not comparable, preserve original order
                return json.dumps(data, separators=(',', ':'))
        elif isinstance(data, (str, int, float, bool, type(None))):
            return json.dumps(data, separators=(',', ':'))
        else:
            # Convert to string representation
            return json.dumps(str(data), separators=(',', ':'))
    
    def _sort_dict_recursive(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Recursively sort dictionary keys for deterministic ordering"""
        result = {}
        for key in sorted(data.keys()):
            value = data[key]
            if isinstance(value, dict):
                result[key] = self._sort_dict_recursive(value)
            elif isinstance(value, list):
                result[key] = [
                    self._sort_dict_recursive(item) if isinstance(item, dict) else item
                    for item in value
                ]
            else:
                result[key] = value
        return result
    
    def compute_hash(self, data: Any) -> HashResult:
        """
        Compute deterministic hash of data
        
        Args:
            data: Data to hash
            
        Returns:
            HashResult with hash value and metadata
        """
        normalized = self.normalize_data(data)
        hash_value = self.hash_func(normalized.encode('utf-8')).hexdigest()
        
        return HashResult(
            hash_value=hash_value,
            algorithm=self.algorithm,
            input_size=len(normalized),
            normalized_input=normalized
        )
    
    def compute_hash_string(self, data: Any) -> str:
        """
        Compute hash and return only the hash string
        
        Args:
            data: Data to hash
            
        Returns:
            Hash string
        """
        return self.compute_hash(data).hash_value

class ExecutionHashGenerator:
    """Specialized hash generator for execution traceability"""
    
    def __init__(self):
        self.hasher = DeterministicHasher("sha256")
    
    def generate_input_hash(self, module_id: str, intent: str, user_id: str, data: Dict[str, Any]) -> str:
        """
        Generate hash for execution input
        
        Args:
            module_id: Module identifier
            intent: Execution intent
            user_id: User identifier
            data: Input data
            
        Returns:
            Input hash string
        """
        input_payload = {
            "module_id": module_id,
            "intent": intent,
            "user_id": user_id,
            "data": data
        }
        return self.hasher.compute_hash_string(input_payload)
    
    def generate_output_hash(self, response: Dict[str, Any]) -> str:
        """
        Generate hash for execution output
        
        Args:
            response: Response data
            
        Returns:
            Output hash string
        """
        # Extract only the result portion to avoid metadata noise
        output_payload = {
            "status": response.get("status"),
            "result": response.get("result", {})
        }
        return self.hasher.compute_hash_string(output_payload)
    
    def generate_semantic_hash(self, module_id: str, intent: str, input_hash: str, output_hash: str) -> str:
        """
        Generate semantic hash for execution replay validation
        
        Args:
            module_id: Module identifier
            intent: Execution intent
            input_hash: Input hash
            output_hash: Output hash
            
        Returns:
            Semantic hash string
        """
        semantic_payload = {
            "module_id": module_id,
            "intent": intent,
            "input_hash": input_hash,
            "output_hash": output_hash
        }
        return self.hasher.compute_hash_string(semantic_payload)
    
    def generate_execution_fingerprint(
        self,
        module_id: str,
        intent: str,
        user_id: str,
        input_data: Dict[str, Any],
        output_data: Dict[str, Any]
    ) -> Dict[str, str]:
        """
        Generate complete set of hashes for an execution
        
        Args:
            module_id: Module identifier
            intent: Execution intent
            user_id: User identifier
            input_data: Input data
            output_data: Output data
            
        Returns:
            Dictionary with all hash types
        """
        input_hash = self.generate_input_hash(module_id, intent, user_id, input_data)
        output_hash = self.generate_output_hash(output_data)
        semantic_hash = self.generate_semantic_hash(module_id, intent, input_hash, output_hash)
        
        return {
            "input_hash": input_hash,
            "output_hash": output_hash,
            "semantic_hash": semantic_hash
        }

class ReplayHashValidator:
    """Validates execution replay using hash comparison"""
    
    def __init__(self):
        self.generator = ExecutionHashGenerator()
    
    def validate_replay(
        self,
        original_execution: Dict[str, Any],
        replay_execution: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate that replay execution matches original
        
        Args:
            original_execution: Original execution data
            replay_execution: Replay execution data
            
        Returns:
            Validation result
        """
        # Extract hashes from original
        original_hashes = {
            "input_hash": original_execution.get("input_hash"),
            "output_hash": original_execution.get("output_hash"),
            "semantic_hash": original_execution.get("semantic_hash")
        }
        
        # Generate hashes for replay
        replay_hashes = self.generator.generate_execution_fingerprint(
            module_id=replay_execution["module_id"],
            intent=replay_execution["intent"],
            user_id=replay_execution["user_id"],
            input_data=replay_execution["input_data"],
            output_data=replay_execution["output_data"]
        )
        
        # Compare hashes
        validation_result = {
            "valid": True,
            "hash_comparisons": {},
            "mismatches": []
        }
        
        for hash_type in ["input_hash", "output_hash", "semantic_hash"]:
            original_hash = original_hashes.get(hash_type)
            replay_hash = replay_hashes.get(hash_type)
            
            match = original_hash == replay_hash
            validation_result["hash_comparisons"][hash_type] = {
                "original": original_hash,
                "replay": replay_hash,
                "match": match
            }
            
            if not match:
                validation_result["valid"] = False
                validation_result["mismatches"].append(hash_type)
        
        return validation_result
    
    def generate_replay_signature(self, execution_data: Dict[str, Any]) -> str:
        """
        Generate replay signature for execution
        
        Args:
            execution_data: Execution data
            
        Returns:
            Replay signature hash
        """
        signature_payload = {
            "module_id": execution_data["module_id"],
            "intent": execution_data["intent"],
            "input_hash": execution_data.get("input_hash"),
            "output_hash": execution_data.get("output_hash"),
            "timestamp": execution_data.get("timestamp_utc")
        }
        return self.generator.hasher.compute_hash_string(signature_payload)