"""
InsightFlow Adapter for Analytics/Metrics Integration
"""

from .base_adapter import BaseIntegrationAdapter
from typing import Any, Dict, Optional
import logging
import requests
from datetime import datetime
import os

logger = logging.getLogger(__name__)

class InsightFlowAdapter(BaseIntegrationAdapter):
    """
    Adapter for integrating with InsightFlow (Analytics/Metrics System).
    
    This adapter handles:
    - Metrics collection and reporting
    - Analytics event logging
    - Performance data transmission
    - Secure API communication with authentication
    - Tenant-aware data isolation
    """
    
    def _execute_internal(self, event: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """
        Execute InsightFlow-specific integration logic.
        
        Args:
            event: Event data containing information about the action that occurred
            
        Returns:
            Result of the InsightFlow integration, or None if not applicable
        """
        action = event.get('action', '')
        tenant_id = event.get('tenant_id', 'unknown')
        user_id = event.get('user_id', 'unknown')
        
        # Process analytics-relevant events for InsightFlow
        logger.info(f"Processing {action} event for InsightFlow analytics (tenant: {tenant_id})")
        
        # Validate tenant access before proceeding
        if not self._validate_tenant_access(tenant_id, user_id):
            logger.warning(f"Tenant access validation failed for tenant {tenant_id}")
            return {
                'adapter': 'insightflow',
                'event_action': action,
                'success': False,
                'error': 'Tenant access validation failed',
                'response': None
            }
        
        # Send metrics to InsightFlow system
        insightflow_response = self._send_metrics_to_insightflow(event)
        
        return {
            'adapter': 'insightflow',
            'event_action': action,
            'success': insightflow_response.get('status') in ['recorded', 'success'],
            'response': insightflow_response,
            'tenant_id': tenant_id
        }
    
    def _validate_tenant_access(self, tenant_id: str, user_id: str) -> bool:
        """
        Validate that the user has access to the specified tenant
        In a real implementation, this would check permissions against the RBAC system
        """
        # For now, assume access is valid if both IDs exist
        return bool(tenant_id and user_id)
    
    def _send_metrics_to_insightflow(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Send metrics to the InsightFlow system via API call.
        
        Args:
            event: Event data to extract metrics from
            
        Returns:
            Response from InsightFlow system
        """
        try:
            # Get InsightFlow API configuration from adapter config
            insightflow_api_url = self.config.get('insightflow_api_url', os.getenv('INSIGHTFLOW_API_URL'))
            insightflow_api_key = self.config.get('insightflow_api_key', os.getenv('INSIGHTFLOW_API_KEY'))
            
            if not insightflow_api_url or not insightflow_api_key:
                logger.warning("InsightFlow API configuration not found, using simulation mode")
                return self._simulate_insightflow_response(event)
            
            # Prepare headers with authentication
            headers = {
                'Authorization': f'Bearer {insightflow_api_key}',
                'Content-Type': 'application/json',
                'X-Tenant-ID': event.get('tenant_id', 'unknown'),
                'X-Request-ID': event.get('event_id', 'unknown')
            }
            
            # Prepare metrics payload
            metrics_payload = {
                'event_id': event.get('event_id'),
                'action': event.get('action'),
                'tenant_id': event.get('tenant_id'),
                'user_id': event.get('user_id'),
                'data': event,
                'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
                'metrics': {
                    'action_type': event.get('action', 'unknown'),
                    'duration_ms': event.get('duration_ms', 0),
                    'resource_type': event.get('resource_type', 'general'),
                    'user_role': event.get('user_role', 'unknown')
                }
            }
            
            # Make API call to InsightFlow system
            logger.info(f"Sending metrics to InsightFlow for {event.get('action')} at {insightflow_api_url}")
            response = requests.post(
                f"{insightflow_api_url}/metrics",
                json=metrics_payload,
                headers=headers,
                timeout=30
            )
            
            # Process response
            if response.status_code in [200, 201]:
                response_data = response.json()
                logger.info(f"Successfully sent metrics to InsightFlow: {response_data.get('metric_id', 'unknown')}" )
                return {
                    'status': 'recorded',
                    'metric_id': response_data.get('metric_id', f"insight_{event.get('event_id', 'unknown')}") ,
                    'timestamp': datetime.utcnow().isoformat(),
                    'processed': True,
                    'raw_response': response_data
                }
            else:
                logger.error(f"InsightFlow API returned status {response.status_code}: {response.text}")
                return {
                    'status': 'error',
                    'error_code': response.status_code,
                    'error_message': response.text,
                    'timestamp': datetime.utcnow().isoformat(),
                    'processed': False
                }
        
        except requests.exceptions.Timeout:
            logger.error("InsightFlow API request timed out")
            return {
                'status': 'error',
                'error_code': 'timeout',
                'error_message': 'Request timed out',
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"InsightFlow API request failed: {str(e)}")
            return {
                'status': 'error',
                'error_code': 'request_failed',
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
        except Exception as e:
            logger.error(f"Unexpected error sending metrics to InsightFlow: {str(e)}")
            return {
                'status': 'error',
                'error_code': 'unexpected_error',
                'error_message': str(e),
                'timestamp': datetime.utcnow().isoformat(),
                'processed': False
            }
    
    def _simulate_insightflow_response(self, event: Dict[str, Any]) -> Dict[str, Any]:
        """
        Simulate InsightFlow response when API configuration is not available
        """
        logger.info(f"Simulating InsightFlow response for {event.get('action')} event")
        
        return {
            'status': 'recorded',
            'metric_id': f"insight_sim_{event.get('event_id', 'unknown')}",
            'timestamp': event.get('timestamp', datetime.utcnow().isoformat()),
            'processed': True,
            'simulation': True
        }


# Example configuration for this adapter:
# {
#     "name": "InsightFlow Adapter",
#     "enabled": True,
#     "insightflow_api_url": "https://insightflow-api.example.com",
#     "insightflow_api_key": "your-insightflow-key"
# }