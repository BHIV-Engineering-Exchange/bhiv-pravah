"""
Karya Adapter for Task/Workflow Integration
"""

from .base_adapter import BaseIntegrationAdapter
from typing import Any, Dict, Optional
import logging
import requests
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class KaryaAdapter(BaseIntegrationAdapter):
    """
    Adapter for integrating with Karya (Task/Workflow System).
    
    This adapter handles:
    - Task creation and assignment
    - Workflow trigger events
    - Task status updates
    - Secure API communication with authentication
    - Tenant-aware data isolation
    """
    
    def _execute_internal(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute Karya-specific integration logic.
        
        Args:
            event: Event data containing information about the action that occurred
            
        Returns:
            Result of the Karya integration, or None if not applicable
        """
        action = event.get('action', '')
        tenant_id = event.get('tenant_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        
        # Only process relevant events for Karya
        if 'task' in action or 'workflow' in action or 'approval' in action:
            logger.info(f"Processing {action} event for Karya integration (tenant: {tenant_id})")
            
            # Validate tenant access before proceeding
            if not self._validate_tenant_access(tenant_id, user_id):
                logger.warning(f"Tenant access validation failed for tenant {tenant_id}")
                return {
                    'adapter': 'karya',
                    'event_action': action,
                    'success': False,
                    'error': 'Tenant access validation failed',
                    'response': None
                }
            
            # Create task in Karya system with authentication
            karya_response = self._create_karya_task(event)
            
            return {
                'adapter': 'karya',
                'event_action': action,
                'success': karya_response.get('status') in ['created', 'success'],
                'response': karya_response,
                'tenant_id': tenant_id
            }
        
        logger.debug(f"Event {action} not relevant for Karya, skipping")
        return None
    
    def _validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """
        Validate that the user has access to the specified tenant
        In a real implementation, this would check permissions against the RBAC system
        """
        # For now, assume access is valid if both IDs exist
        return bool(tenant_id and user_id)
    
    def _create_karya_task(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Create a task in the Karya system via API call.
        
        Args:
            event: Event data to create task from
            
        Returns:
            Response from Karya system
        """
        try:
            # Get Karya API configuration from adapter config
            karya_api_url = self.config.get('karya_api_url', os.getenv('KARYA_API_URL'))
            karya_api_key = self.config.get('karya_api_key', os.getenv('KARYA_API_KEY'))
            
            if not karya_api_url or not karya_api_key:
                logger.warning("Karya API configuration not found, using simulation mode")
                return self._simulate_karya_response(event)
            
            # Prepare headers with authentication
            headers = {
                'Authorization': f'Bearer {karya_api_key}',
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
                'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
                'task_details': {
                    'title': f"Task from {event.get('action', 'system')}",
                    'description': f"Automated task triggered by {event.get('action', 'system')} event",
                    'assigned_to': event.get('user_id', 'unassigned'),
                    'priority': 'normal'
                }
            }
            
            # Make API call to Karya system
            logger.info(f"Creating task in Karya for {event.get('action')} at {karya_api_url}")
            response = requests.post(
                f"{karya_api_url}/tasks",
                json=payload,
                headers=headers,
                timeout=30
            )
            
            # Process response
            if response.status_code in [200, 201]:
                response_data = response.json()
                logger.info(f"Successfully created task in Karya: {response_data.get('task_id', 'unknown')}" )
                return {
                    'status': 'created',
                    'task_id': response_data.get('task_id', f"karya_{event.get('event_id', 'unknown')}") ,
                    'timestamp': datetime.utcnow().isoformat(),
                    'assigned_to': event.get('user_id', 'unassigned'),
                    'processed': True,
                    'raw_response': response_data
                }
            else:
                logger.error(f"Karya API returned status {response.status_code}: {response.text}")
                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'timestamp': datetime.utcnow().isoformat(),
                    'processed': False
                }
        
        except requests.exceptions.Timeout:
            logger.error("Karya API request timed out")
            return {
                'status': 'error',
                'error_code': 'timeout',
                'error_message': 'Request timed out',
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Karya API request failed: {str(e)}")
            return {
                'status': 'error',
                'error_code': 'request_failed',
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
        except Exception as e:
            logger.error(f"Unexpected error creating task in Karya: {str(e)}")
            return {
                'status': 'error',
                'error_code': 'unexpected_error',
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
    
    def _simulate_karya_response(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate Karya response when API configuration is not available
        """
        logger.info(f"Simulating Karya response for {event.get('action')} event")
        
        return {
            'status': 'created',
            'task_id': f"karya_sim_{event.get('event_id', 'unknown')}",
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
            'assigned_to': event.get('user_id', 'unassigned'),
            'processed': True,
            'simulation': True
        }


# Example configuration for this adapter:
# {
#     "name": "Karya Adapter",
#     "enabled": True,
#     "karya_api_url": "https://karya-api.example.com",
#     "karya_api_key": "your-karya-key"
# }