"""
Compatibility Service for handling API versioning and backward compatibility.

This service manages version detection, request routing, and format conversion
between different API versions.
"""

import logging
from typing import Dict, Any, Optional, Tuple
from app.adapters.interface_converter import InterfaceConverter
from app.services.validation_service import validation_service

logger = logging.getLogger(__name__)


class CompatibilityService:
    """Service for API version compatibility management"""
    
    def __init__(self):
        self.converter = InterfaceConverter
    
    def detect_api_version(self, request_data: Dict[str, Any]) -> str:
        """
        Detect API version based on request structure.
        
        Args:
            request_data: Request data to analyze
            
        Returns:
            Detected API version ('v1', 'v2', 'ksml')
        """
        try:
            # Check for KSML structure
            if self._is_ksml_format(request_data):
                return "ksml"
            
            # Check for Core v2 structure
            if self._is_core_v2_format(request_data):
                return "v2"
            
            # Default to v1 legacy format
            return "v1"
            
        except Exception as e:
            logger.warning(f"Version detection error: {e}, defaulting to v1")
            return "v1"
    
    def _is_ksml_format(self, data: Dict[str, Any]) -> bool:
        """Check if data matches KSML format"""
        return (
            isinstance(data, dict) and
            "meta" in data and
            "payload" in data and
            isinstance(data.get("meta"), dict) and
            "packet_type" in data.get("meta", {})
        )
    
    def _is_core_v2_format(self, data: Dict[str, Any]) -> bool:
        """Check if data matches Core v2 format"""
        return (
            isinstance(data, dict) and
            "task_type" in data and
            "min_confidence" in data
        )
    
    def convert_to_legacy_format(
        self, 
        request_data: Dict[str, Any], 
        source_version: str
    ) -> Dict[str, Any]:
        """
        Convert request to legacy v1 format for processing.
        
        Args:
            request_data: Request data to convert
            source_version: Source API version
            
        Returns:
            Legacy v1 format request
        """
        try:
            if source_version == "v2":
                # Convert Core v2 to legacy v1
                return self.converter.core_to_insight_flow(request_data)
            elif source_version == "ksml":
                # Extract data from KSML and convert
                from app.adapters.ksml_adapter import KSMLAdapter
                core_data = KSMLAdapter.unwrap(request_data)
                return self.converter.core_to_insight_flow(core_data)
            else:
                # Already v1 format
                return request_data
                
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            raise ValueError(f"Failed to convert from {source_version} to v1: {str(e)}")
    
    def convert_from_legacy_format(
        self, 
        response_data: Dict[str, Any], 
        target_version: str
    ) -> Dict[str, Any]:
        """
        Convert legacy v1 response to target format.
        
        Args:
            response_data: Legacy v1 response data
            target_version: Target API version
            
        Returns:
            Converted response in target format
        """
        try:
            if target_version == "v2":
                # Convert legacy v1 to Core v2
                return self.converter.insight_flow_to_core(response_data)
            elif target_version == "ksml":
                # Convert to Core then wrap in KSML
                from app.adapters.ksml_adapter import KSMLAdapter, KSMLPacketType
                core_data = self.converter.insight_flow_to_core(response_data)
                return KSMLAdapter.wrap(core_data, KSMLPacketType.ROUTING_RESPONSE)
            else:
                # Already v1 format
                return response_data
                
        except Exception as e:
            logger.error(f"Format conversion error: {e}")
            raise ValueError(f"Failed to convert from v1 to {target_version}: {str(e)}")
    
    def validate_version_compatibility(
        self, 
        request_data: Dict[str, Any], 
        expected_version: str
    ) -> Tuple[bool, str]:
        """
        Validate that request matches expected API version.
        
        Args:
            request_data: Request data to validate
            expected_version: Expected API version
            
        Returns:
            Tuple of (is_compatible, error_message)
        """
        detected_version = self.detect_api_version(request_data)
        
        if detected_version == expected_version:
            return True, ""
        
        # Check if conversion is possible
        try:
            if expected_version == "v1":
                self.convert_to_legacy_format(request_data, detected_version)
            else:
                # Convert to v1 first, then to target
                legacy_data = self.convert_to_legacy_format(request_data, detected_version)
                self.convert_from_legacy_format(legacy_data, expected_version)
            
            return True, f"Auto-converted from {detected_version} to {expected_version}"
            
        except Exception as e:
            return False, f"Incompatible version: detected {detected_version}, expected {expected_version}. {str(e)}"
    
    def get_version_info(self) -> Dict[str, Any]:
        """
        Get information about supported API versions.
        
        Returns:
            Version information dictionary
        """
        return {
            "supported_versions": ["v1", "v2"],
            "supported_formats": ["insightflow", "core", "ksml"],
            "default_version": "v1",
            "latest_version": "v2",
            "deprecation_notice": {
                "v1": "Legacy format, maintained for backward compatibility",
                "v2": "Current format with Core integration and KSML support"
            },
            "conversion_support": {
                "v1_to_v2": True,
                "v2_to_v1": True,
                "ksml_support": True
            }
        }


# Global compatibility service instance
compatibility_service = CompatibilityService()