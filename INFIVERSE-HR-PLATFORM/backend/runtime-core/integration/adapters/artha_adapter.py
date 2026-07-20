"""
Artha Adapter for Payroll/Finance Integration
"""

from .base_adapter import BaseIntegrationAdapter
from typing import Any, Dict, Optional
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

class ArthaAdapter(BaseIntegrationAdapter):
    """
    Adapter for integrating with Artha (Payroll/Finance System).
    
    This adapter handles:
    - Payroll data synchronization
    - Finance event notifications
    - Transaction logging to Artha
    - Secure API communication with authentication
    - Tenant-aware data isolation
    """
    
    def _execute_internal(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute Artha-specific integration logic.
        
        Args:
            event: Event data containing information about the action that occurred
            
        Returns:
            Result of the Artha integration, or None if not applicable
        """
        action = event.get('action', '')
        tenant_id = event.get('tenant_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        
        # Only process relevant events for Artha
        if 'payroll' in action or 'salary' in action or 'finance' in action:
            logger.info(f"Processing {action} event for Artha integration (tenant: {tenant_id})")
            
            # Validate tenant access before proceeding
            if not self._validate_tenant_access(tenant_id, user_id):
                logger.warning(f"Tenant access validation failed for tenant {tenant_id}")
                return {
                    'adapter': 'artha',
                    'event_action': action,
                    'success': False,
                    'error': 'Tenant access validation failed',
                    'response': None
                }
            
            # Send data to Artha system with authentication
            artha_response = self._send_to_artha(event)
            
            return {
                'adapter': 'artha',
                'event_action': action,
                'success': artha_response.get('status') == 'success',
                'response': artha_response,
                'tenant_id': tenant_id
            }
        
        logger.debug(f"Event {action} not relevant for Artha, skipping")
        return None
    
    def _validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """
        Validate that the user has access to the specified tenant
        In a real implementation, this would check permissions against the RBAC system
        """
        # For now, assume access is valid if both IDs exist
        return bool(tenant_id and user_id)
    
    def _send_to_artha(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send event data to the Artha system via API call.
        
        Args:
            event: Event data to send to Artha
            
        Returns:
            Response from Artha system
        """
        try:
            # Get Artha API configuration from adapter config
            artha_api_url = self.config.get('artha_api_url', os.getenv('ARTHA_API_URL'))
            artha_api_key = self.config.get('artha_api_key', os.getenv('ARTHA_API_KEY'))
            
            if not artha_api_url or not artha_api_key:
                logger.warning("Artha API configuration not found, using simulation mode")
                return self._simulate_artha_response(event)
            
            # Prepare headers with authentication
            headers = {
                'Authorization': f'Bearer {artha_api_key}',
                'Content-Type': 'application/json',
                'X-Tenant-ID': event.get('tenant_id', 'unknown'),
                'X-Request-ID': event.get('event_id', 'unknown')
            }
            
            # Prepare payload
            payload = {
                'event_id': event.get('event_id'),
                'action': event.get('action'),
                'tenant_id': event.get('tenant_id'),
                'user_id': event.get('user_id'),
                'data': event,
                'timestamp': event.get('timestamp', datetime.utcnow().isoformat())
            }
            
            # Make API call to Artha system
            logger.info(f"Sending {event.get('action')} to Artha API: {artha_api_url}")
            response = requests.post(
                f"{artha_api_url}/events",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Process response
            if response.status_code in [200, 201]:
                response_data = response.json()
                logger.info(f"Successfully sent to Artha: {response_data.get('transaction_id', 'unknown')}" )
                return {
                    'status': 'success',
                    'transaction_id': response_data.get('transaction_id', f"artha_{event.get('event_id', 'unknown')}") ,
                    'timestamp': datetime.utcnow().isoformat(),
                    'processed': True,
                    'raw_response': response_data
                }
            else:
                logger.error(f"Artha API returned status {response.status_code}: {response.text}")
                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'timestamp': datetime.utcnow().isoformat(),
                    'processed': False
                }
        
        except requests.exceptions.Timeout:
            logger.error("Artha API request timed out")
            return {
                'status': 'error',
                'error_code': 'timeout',
                'error_message': 'Request timed out',
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Artha API request failed: {str(e)}")
            return {
                'status': 'error',
                'error_code': 'request_failed',
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
        except Exception as e:
            logger.error(f"Unexpected error sending to Artha: {str(e)}")
            return {
                'status': 'error',
                'error_code': 'unexpected_error',
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
    
    def _simulate_artha_response(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Artha response when API configuration is not available
        """
        logger.info(f"Simulating Artha response for {event.get('action')} event")
        
        return {
            'status': 'success',
            'transaction_id': f"artha_sim_{event.get('event_id', 'unknown')}",
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
            'processed': True,
            'simulation': True
        }


# Example configuration for this adapter:
# {
#     "name": "Artha Adapter",
#     "enabled": True,
#     "artha_api_url": "https://artha-api.example.com",
#     "artha_api_key": "your-artha-key"
# }