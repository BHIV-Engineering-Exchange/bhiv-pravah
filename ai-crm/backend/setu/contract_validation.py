from datetime import datetime
from typing import Any, Dict, Optional


class ContractValidationError(Exception):
    def __init__(self, code: str, message: str, details: Optional[Dict[str, Any]] = None):
        super().__init__(message)
        self.code = code
        self.message = message
        self.details = details or {}


class ContractValidator:
    """Validates contracts between Niyantran Event -> Sampada Signal -> SETU"""
    
    REQUIRED_CONTRACT_FIELDS = [
        "trace_id",
        "entity_id", 
        "event_type",
        "timestamp",
        "tenant_id"
    ]
    
    def __init__(self):
        pass

    def validate_niyantran_to_sampada_contract(
        self, 
        niyantran_event: Dict[str, Any], 
        sampada_signal: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate contract between Niyantran event and Sampada signal"""
        
        validation_result = {
            "valid": True,
            "violations": [],
            "validation_id": f"niy_sam_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Validate trace_id preservation
        if niyantran_event.get("trace_id") != sampada_signal.get("trace_id"):
            validation_result["valid"] = False
            validation_result["violations"].append({
                "field": "trace_id",
                "violation_type": "mismatch",
                "niyantran_value": niyantran_event.get("trace_id"),
                "sampada_value": sampada_signal.get("trace_id")
            })
        
        # Validate entity_id preservation  
        if niyantran_event.get("entity_id") != sampada_signal.get("entity_id"):
            validation_result["valid"] = False
            validation_result["violations"].append({
                "field": "entity_id", 
                "violation_type": "mismatch",
                "niyantran_value": niyantran_event.get("entity_id"),
                "sampada_value": sampada_signal.get("entity_id")
            })
        
        # Validate event_type preservation
        if niyantran_event.get("event_type") != sampada_signal.get("event_type"):
            validation_result["valid"] = False
            validation_result["violations"].append({
                "field": "event_type",
                "violation_type": "mismatch", 
                "niyantran_value": niyantran_event.get("event_type"),
                "sampada_value": sampada_signal.get("event_type")
            })
        
        # Validate tenant_id preservation
        if niyantran_event.get("tenant_id") != sampada_signal.get("tenant_id"):
            validation_result["valid"] = False
            validation_result["violations"].append({
                "field": "tenant_id",
                "violation_type": "mismatch",
                "niyantran_value": niyantran_event.get("tenant_id"),
                "sampada_value": sampada_signal.get("tenant_id")
            })
        
        # Validate timestamp chronology (Sampada should be after Niyantran)
        try:
            niy_time = datetime.fromisoformat(niyantran_event["timestamp"].replace("Z", "+00:00"))
            sam_time = datetime.fromisoformat(sampada_signal["timestamp"].replace("Z", "+00:00"))
            
            if sam_time < niy_time:
                validation_result["valid"] = False
                validation_result["violations"].append({
                    "field": "timestamp",
                    "violation_type": "chronology_violation",
                    "niyantran_timestamp": niyantran_event["timestamp"],
                    "sampada_timestamp": sampada_signal["timestamp"]
                })
        except (ValueError, KeyError, TypeError):
            validation_result["valid"] = False
            validation_result["violations"].append({
                "field": "timestamp",
                "violation_type": "invalid_format",
                "details": "Unable to parse timestamp format"
            })
        
        if not validation_result["valid"]:
            raise ContractValidationError(
                "niyantran_sampada_contract_violation",
                "Contract validation failed between Niyantran and Sampada",
                validation_result
            )
        
        return validation_result

    def validate_sampada_to_setu_contract(
        self,
        sampada_signal: Dict[str, Any],
        setu_ingestion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate contract between Sampada signal and SETU ingestion"""
        
        validation_result = {
            "valid": True,
            "violations": [],
            "validation_id": f"sam_set_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Validate all required fields are preserved
        for field in self.REQUIRED_CONTRACT_FIELDS:
            if sampada_signal.get(field) != setu_ingestion.get(field):
                validation_result["valid"] = False
                validation_result["violations"].append({
                    "field": field,
                    "violation_type": "field_mismatch",
                    "sampada_value": sampada_signal.get(field),
                    "setu_value": setu_ingestion.get(field)
                })
        
        # Check for missing required fields
        missing_fields = []
        for field in self.REQUIRED_CONTRACT_FIELDS:
            if field not in setu_ingestion:
                missing_fields.append(field)
        
        if missing_fields:
            validation_result["valid"] = False
            validation_result["violations"].append({
                "violation_type": "missing_required_fields",
                "missing_fields": missing_fields
            })
        
        if not validation_result["valid"]:
            raise ContractValidationError(
                "sampada_setu_contract_violation",
                "Contract validation failed between Sampada and SETU",
                validation_result
            )
        
        return validation_result

    def validate_end_to_end_contract(
        self,
        niyantran_event: Dict[str, Any],
        sampada_signal: Dict[str, Any], 
        setu_ingestion: Dict[str, Any]
    ) -> Dict[str, Any]:
        """Validate end-to-end contract from Niyantran -> Sampada -> SETU"""
        
        validation_result = {
            "valid": True,
            "validations": [],
            "validation_id": f"e2e_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}"
        }
        
        # Validate Niyantran -> Sampada
        try:
            niy_sam_result = self.validate_niyantran_to_sampada_contract(niyantran_event, sampada_signal)
            validation_result["validations"].append({
                "stage": "niyantran_to_sampada",
                "result": niy_sam_result
            })
        except ContractValidationError as e:
            validation_result["valid"] = False
            validation_result["validations"].append({
                "stage": "niyantran_to_sampada", 
                "result": {"valid": False, "error": e.details}
            })
        
        # Validate Sampada -> SETU
        try:
            sam_set_result = self.validate_sampada_to_setu_contract(sampada_signal, setu_ingestion)
            validation_result["validations"].append({
                "stage": "sampada_to_setu",
                "result": sam_set_result
            })
        except ContractValidationError as e:
            validation_result["valid"] = False
            validation_result["validations"].append({
                "stage": "sampada_to_setu",
                "result": {"valid": False, "error": e.details}
            })
        
        if not validation_result["valid"]:
            raise ContractValidationError(
                "end_to_end_contract_violation",
                "End-to-end contract validation failed",
                validation_result
            )
        
        return validation_result

    def validate_incomplete_contract(self, contract_data: Dict[str, Any]) -> None:
        """Reject incomplete contracts"""
        
        missing_fields = []
        for field in self.REQUIRED_CONTRACT_FIELDS:
            if field not in contract_data or contract_data[field] is None:
                missing_fields.append(field)
        
        if missing_fields:
            raise ContractValidationError(
                "incomplete_contract",
                "Contract is incomplete",
                {
                    "missing_fields": missing_fields,
                    "required_fields": self.REQUIRED_CONTRACT_FIELDS
                }
            )