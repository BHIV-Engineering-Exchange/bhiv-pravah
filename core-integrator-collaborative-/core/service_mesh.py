"""
Service Mesh for BHIV Core-Integrator
Handles resilient inter-service communication with circuit breaker pattern
"""

import requests
import time
import logging
import json
from typing import Dict, Any, Optional, Callable
from enum import Enum
from datetime import datetime, timedelta
from functools import wraps
import traceback

try:
    from config import ConfigManager
except ImportError:
    # For testing purposes
    class ConfigManager:
        @staticmethod
        def get_config():
            return {
                'services': {
                    'prompt_runner': {'port': 8003, 'timeout': 30},
                    'creator_core': {'port': 8000, 'timeout': 30},
                    'bhiv_core': {'port': 8001, 'timeout': 30},
                    'integration_bridge': {'port': 8004, 'timeout': 30},
                    'bucket': {'port': 8005, 'timeout': 30},
                    'cet': {'port': 8006, 'timeout': 30},
                    'sarathi': {'port': 8007, 'timeout': 30},
                    'gate': {'port': 8008, 'timeout': 30},
                },
                'global': {'request_timeout': 30}
            }
        
        @staticmethod
        def get_service(name):
            config = ConfigManager.get_config()
            return config['services'].get(name, {})
        
        @staticmethod
        def get_service_url(name):
            urls = {
                'prompt_runner': 'http://127.0.0.1:8003',
                'creator_core': 'http://127.0.0.1:8000',
                'bhiv_core': 'http://127.0.0.1:8001',
                'integration_bridge': 'http://127.0.0.1:8004',
                'bucket': 'http://127.0.0.1:8005',
                'cet': 'http://127.0.0.1:8006',
                'sarathi': 'http://127.0.0.1:8007',
                'gate': 'http://127.0.0.1:8008',
            }
            return urls.get(name)
        
        @staticmethod
        def get_service_timeout(name):
            return 30


logger = logging.getLogger(__name__)


class CircuitState(Enum):
    """Circuit breaker states"""
    CLOSED = "closed"          # Normal operation
    OPEN = "open"              # Service is down, reject requests
    HALF_OPEN = "half_open"    # Testing if service recovered


class CircuitBreaker:
    """
    Circuit Breaker Pattern Implementation
    Protects against cascading failures
    """
    
    def __init__(
        self,
        failure_threshold: int = 5,
        success_threshold: int = 2,
        timeout_seconds: int = 60,
        name: str = "CircuitBreaker"
    ):
        """
        Initialize circuit breaker
        
        Args:
            failure_threshold: Failures before opening circuit
            success_threshold: Successes before closing circuit (in half-open state)
            timeout_seconds: Time to wait before trying half-open
            name: Circuit breaker name (for logging)
        """
        self.failure_threshold = failure_threshold
        self.success_threshold = success_threshold
        self.timeout_seconds = timeout_seconds
        self.name = name
        
        # State tracking
        self.state = CircuitState.CLOSED
        self.failure_count = 0
        self.success_count = 0
        self.last_failure_time = None
        self.last_attempt_time = None
    
    def call(self, func: Callable, *args, **kwargs) -> Any:
        """
        Execute function with circuit breaker protection
        
        Args:
            func: Function to call
            *args: Function arguments
            **kwargs: Function keyword arguments
            
        Returns:
            Function result
            
        Raises:
            Exception: If circuit is open or function fails
        """
        if self.state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self.state = CircuitState.HALF_OPEN
                self.success_count = 0
                logger.warning(f"[{self.name}] Circuit entering HALF_OPEN state")
            else:
                raise Exception(
                    f"Circuit breaker OPEN for {self.name}. "
                    f"Service unavailable. Retry after {self._time_until_reset():.1f}s"
                )
        
        try:
            result = func(*args, **kwargs)
            self._on_success()
            return result
        except Exception as e:
            self._on_failure()
            raise
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time passed to try reset"""
        if self.last_failure_time is None:
            return False
        
        time_since_failure = datetime.now() - self.last_failure_time
        return time_since_failure.total_seconds() >= self.timeout_seconds
    
    def _time_until_reset(self) -> float:
        """Get seconds until circuit can attempt reset"""
        if self.last_failure_time is None:
            return 0
        
        time_since_failure = datetime.now() - self.last_failure_time
        remaining = self.timeout_seconds - time_since_failure.total_seconds()
        return max(0, remaining)
    
    def _on_success(self):
        """Handle successful request"""
        if self.state == CircuitState.HALF_OPEN:
            self.success_count += 1
            
            if self.success_count >= self.success_threshold:
                self.state = CircuitState.CLOSED
                self.failure_count = 0
                logger.info(f"[{self.name}] Circuit CLOSED - service recovered [OK]")
        
        elif self.state == CircuitState.CLOSED:
            self.failure_count = 0
    
    def _on_failure(self):
        """Handle failed request"""
        self.failure_count += 1
        self.last_failure_time = datetime.now()
        
        if self.state == CircuitState.HALF_OPEN:
            self.state = CircuitState.OPEN
            logger.error(
                f"[{self.name}] Circuit re-opened - "
                f"service still unavailable"
            )
        
        elif self.state == CircuitState.CLOSED:
            if self.failure_count >= self.failure_threshold:
                self.state = CircuitState.OPEN
                logger.error(
                    f"[{self.name}] Circuit OPEN - "
                    f"threshold ({self.failure_threshold}) exceeded"
                )


class RetryPolicy:
    """Retry policy with exponential backoff"""
    
    def __init__(
        self,
        max_retries: int = 3,
        initial_backoff_ms: int = 100,
        max_backoff_ms: int = 5000,
        backoff_multiplier: float = 2.0,
        retry_on_status_codes: list = None
    ):
        """
        Initialize retry policy
        
        Args:
            max_retries: Maximum retry attempts
            initial_backoff_ms: Initial backoff in milliseconds
            max_backoff_ms: Maximum backoff in milliseconds
            backoff_multiplier: Exponential backoff multiplier
            retry_on_status_codes: HTTP status codes to retry on
        """
        self.max_retries = max_retries
        self.initial_backoff_ms = initial_backoff_ms
        self.max_backoff_ms = max_backoff_ms
        self.backoff_multiplier = backoff_multiplier
        self.retry_on_status_codes = retry_on_status_codes or [408, 429, 500, 502, 503, 504]
    
    def get_backoff_ms(self, attempt: int) -> int:
        """Calculate backoff for retry attempt"""
        backoff = self.initial_backoff_ms * (self.backoff_multiplier ** attempt)
        return min(int(backoff), self.max_backoff_ms)
    
    def should_retry(self, attempt: int, exception: Exception, status_code: Optional[int] = None) -> bool:
        """Determine if request should be retried"""
        if attempt >= self.max_retries:
            return False
        
        # Retry on connection errors
        if isinstance(exception, (requests.ConnectionError, requests.Timeout)):
            return True
        
        # Retry on specific status codes
        if status_code in self.retry_on_status_codes:
            return True
        
        return False


class ServiceMesh:
    """
    Service Mesh for inter-service communication
    Handles:
    - Resilient HTTP calls with retries
    - Circuit breaker pattern
    - Health checks
    - Service discovery via ConfigManager
    """
    
    def __init__(self):
        """Initialize service mesh"""
        self.circuit_breakers: Dict[str, CircuitBreaker] = {}
        self.retry_policy = RetryPolicy(max_retries=3)
        self.service_health: Dict[str, Dict[str, Any]] = {}
        self._initialize_circuit_breakers()
    
    def _initialize_circuit_breakers(self):
        """Create circuit breakers for all services"""
        try:
            config = ConfigManager.get_config()
            services = config.get('services', {})
        except:
            services = {
                'prompt_runner': {},
                'creator_core': {},
                'bhiv_core': {},
                'integration_bridge': {},
                'bucket': {}
            }
        
        for service_name in services:
            self.circuit_breakers[service_name] = CircuitBreaker(
                failure_threshold=5,
                success_threshold=2,
                timeout_seconds=60,
                name=service_name
            )
            self.service_health[service_name] = {
                'status': 'unknown',
                'last_check': None,
                'response_time_ms': None
            }
    
    def call_service(
        self,
        service_name: str,
        endpoint: str,
        method: str = 'POST',
        data: Optional[Dict[str, Any]] = None,
        params: Optional[Dict[str, Any]] = None,
        headers: Optional[Dict[str, str]] = None,
        timeout: Optional[int] = None,
        use_circuit_breaker: bool = True
    ) -> Dict[str, Any]:
        """
        Make resilient call to another service
        
        Args:
            service_name: Name of service to call
            endpoint: API endpoint (e.g., "/execute")
            method: HTTP method (GET, POST, etc.)
            data: Request body
            params: Query parameters
            headers: Request headers
            timeout: Request timeout in seconds
            use_circuit_breaker: Use circuit breaker pattern
            
        Returns:
            Response JSON
            
        Raises:
            Exception: If call fails after retries or circuit is open
        """
        service_url = ConfigManager.get_service_url(service_name)
        if not service_url:
            raise ValueError(f"Unknown service: {service_name}")
        
        if timeout is None:
            timeout = ConfigManager.get_service_timeout(service_name)
        
        full_url = f"{service_url}{endpoint}"
        
        # Prepare request
        request_kwargs = {
            'method': method,
            'url': full_url,
            'timeout': timeout,
        }
        
        if data:
            request_kwargs['json'] = data
        if params:
            request_kwargs['params'] = params
        if headers:
            request_kwargs['headers'] = headers
        
        # Execute with circuit breaker and retry logic
        def _execute():
            return self._http_call_with_retry(service_name, request_kwargs)
        
        if use_circuit_breaker:
            circuit_breaker = self.circuit_breakers.get(service_name)
            return circuit_breaker.call(_execute)
        else:
            return _execute()
    
    def _http_call_with_retry(self, service_name: str, request_kwargs: Dict) -> Dict:
        """Execute HTTP call with retry logic"""
        last_exception = None
        
        for attempt in range(self.retry_policy.max_retries + 1):
            try:
                start_time = time.time()
                response = requests.request(**request_kwargs)
                elapsed_ms = (time.time() - start_time) * 1000
                
                # Update health status
                if response.status_code == 200:
                    self.service_health[service_name]['status'] = 'healthy'
                    self.service_health[service_name]['response_time_ms'] = elapsed_ms
                    self.service_health[service_name]['last_check'] = datetime.now()
                
                # Check if we should retry based on status code
                if response.status_code != 200:
                    if self.retry_policy.should_retry(attempt, None, response.status_code):
                        logger.warning(
                            f"[{service_name}] Status {response.status_code}, "
                            f"retry {attempt + 1}/{self.retry_policy.max_retries}"
                        )
                        backoff_ms = self.retry_policy.get_backoff_ms(attempt)
                        time.sleep(backoff_ms / 1000)
                        continue
                
                response.raise_for_status()
                return response.json()
            
            except (requests.ConnectionError, requests.Timeout) as e:
                last_exception = e
                
                self.service_health[service_name]['status'] = 'unavailable'
                self.service_health[service_name]['last_check'] = datetime.now()
                
                if self.retry_policy.should_retry(attempt, e):
                    backoff_ms = self.retry_policy.get_backoff_ms(attempt)
                    logger.warning(
                        f"[{service_name}] {type(e).__name__}, "
                        f"retry {attempt + 1}/{self.retry_policy.max_retries} "
                        f"(backoff: {backoff_ms}ms)"
                    )
                    time.sleep(backoff_ms / 1000)
                    continue
                else:
                    raise
            
            except requests.HTTPError as e:
                last_exception = e
                
                if self.retry_policy.should_retry(attempt, e, e.response.status_code):
                    backoff_ms = self.retry_policy.get_backoff_ms(attempt)
                    logger.warning(
                        f"[{service_name}] HTTP {e.response.status_code}, "
                        f"retry {attempt + 1}/{self.retry_policy.max_retries}"
                    )
                    time.sleep(backoff_ms / 1000)
                    continue
                else:
                    self.service_health[service_name]['status'] = 'error'
                    raise
            
            except Exception as e:
                last_exception = e
                self.service_health[service_name]['status'] = 'error'
                logger.error(f"[{service_name}] Unexpected error: {str(e)}\n{traceback.format_exc()}")
                raise
        
        # All retries exhausted
        if last_exception:
            raise last_exception
    
    def health_check(self, service_name: str) -> bool:
        """
        Check if service is healthy
        
        Args:
            service_name: Name of service to check
            
        Returns:
            True if healthy, False otherwise
        """
        try:
            service_config = ConfigManager.get_service(service_name)
            health_endpoint = service_config.get('health_check_endpoint', '/')
            
            response = requests.get(
                ConfigManager.get_service_url(service_name) + health_endpoint,
                timeout=5
            )
            
            is_healthy = response.status_code == 200
            self.service_health[service_name]['status'] = 'healthy' if is_healthy else 'unhealthy'
            self.service_health[service_name]['last_check'] = datetime.now()
            
            return is_healthy
        except Exception as e:
            self.service_health[service_name]['status'] = 'unavailable'
            self.service_health[service_name]['last_check'] = datetime.now()
            logger.error(f"[{service_name}] Health check failed: {str(e)}")
            return False
    
    def health_check_all(self) -> Dict[str, bool]:
        """Check health of all services"""
        results = {}
        try:
            config = ConfigManager.get_config()
            services = config.get('services', {})
        except:
            services = self.circuit_breakers.keys()
        
        for service_name in services:
            results[service_name] = self.health_check(service_name)
        
        return results
    
    def get_service_status(self) -> Dict[str, Dict[str, Any]]:
        """Get status of all services"""
        return {
            service_name: {
                'health': self.service_health[service_name],
                'circuit_breaker': {
                    'state': self.circuit_breakers[service_name].state.value,
                    'failure_count': self.circuit_breakers[service_name].failure_count,
                }
            }
            for service_name in self.circuit_breakers.keys()
        }
    
    def print_status(self):
        """Print service mesh status (for debugging)"""
        print("\n" + "="*70)
        print("SERVICE MESH STATUS")
        print("="*70)
        
        for service_name, status in self.get_service_status().items():
            health = status['health']['status']
            circuit = status['circuit_breaker']['state']
            response_time = status['health'].get('response_time_ms', 'N/A')
            
            health_icon = "[OK]" if health == "healthy" else "[?]" if health == "unknown" else "[X]"
            circuit_icon = "[CLOSED]" if circuit == "closed" else "[HALF-OPEN]" if circuit == "half_open" else "[OPEN]"
            
            print(
                f"{health_icon} {service_name:20s} | "
                f"Health: {health:12s} | "
                f"Circuit: {circuit:10s} {circuit_icon} | "
                f"Response: {response_time}ms"
            )
        
        print("="*70 + "\n")


# Singleton instance
_service_mesh = None


def get_service_mesh() -> ServiceMesh:
    """Get or create service mesh singleton"""
    global _service_mesh
    if _service_mesh is None:
        _service_mesh = ServiceMesh()
    return _service_mesh


if __name__ == "__main__":
    # Setup logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    
    print("Initializing Service Mesh...")
    mesh = get_service_mesh()
    
    print("\nService Mesh Status:")
    mesh.print_status()
    
    print("\nService URLs:")
    try:
        config = ConfigManager.get_config()
        for service_name in config['services'].keys():
            url = ConfigManager.get_service_url(service_name)
            print(f"  {service_name:20s} → {url}")
    except Exception as e:
        print(f"  Could not load URLs: {e}")
    
    print("\nCircuit Breaker States:")
    for service_name, cb in mesh.circuit_breakers.items():
        print(f"  {service_name:20s} → {cb.state.value}")
