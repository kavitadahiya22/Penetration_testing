"""
Utility functions for cybrty-pentest testing
"""
import asyncio
import time
import httpx
import json
from typing import Callable, Any, Optional, Dict, List
from urllib.parse import urljoin


class APIClient:
    """Simple HTTP client for API testing using httpx"""
    
    def __init__(self, base_url: str, timeout: int = 30):
        self.base_url = base_url.rstrip('/')
        self.timeout = timeout
        self.client = None
    
    async def __aenter__(self):
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.close()
    
    async def close(self):
        """Close the client"""
        if self.client:
            await self.client.aclose()
            self.client = None

    async def _get_client(self):
        """Get or create client"""
        if not self.client:
            self.client = httpx.AsyncClient(timeout=self.timeout)
        return self.client

    async def get(self, endpoint: str, params: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make GET request"""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        client = await self._get_client()
        
        response = await client.get(url, params=params, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def post(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make POST request"""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        client = await self._get_client()
        
        response = await client.post(url, json=data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def put(self, endpoint: str, data: Optional[Dict] = None, **kwargs) -> Dict[str, Any]:
        """Make PUT request"""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        client = await self._get_client()
        
        response = await client.put(url, json=data, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def delete(self, endpoint: str, **kwargs) -> Dict[str, Any]:
        """Make DELETE request"""
        url = urljoin(self.base_url + '/', endpoint.lstrip('/'))
        client = await self._get_client()
        
        response = await client.delete(url, **kwargs)
        response.raise_for_status()
        return response.json()
    
    async def health_check(self) -> bool:
        """Check if API is healthy"""
        try:
            # Try the health endpoint
            health_url = f"{self.base_url}/health"
            client = await self._get_client()
            
            response = await client.get(health_url)
            return response.status_code == 200
        except:
            return False
    
    async def wait_for_ready(self, timeout: int = 60, interval: int = 2) -> bool:
        """Wait for API to be ready"""
        return await wait_for_condition(
            self.health_check,
            timeout=timeout,
            interval=interval,
            description="API readiness check"
        )


async def wait_for_condition(
    condition_func: Callable[[], Any],
    timeout: int = 60,
    interval: int = 2,
    description: str = "condition"
) -> bool:
    """
    Wait for a condition to be true
    
    Args:
        condition_func: Function that returns truthy value when condition is met
        timeout: Maximum time to wait in seconds
        interval: Time between checks in seconds
        description: Description for logging
    
    Returns:
        True if condition was met, False if timeout
    """
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            if asyncio.iscoroutinefunction(condition_func):
                result = await condition_func()
            else:
                result = condition_func()
            
            if result:
                return True
        except Exception as e:
            # Log error but continue waiting
            print(f"Error checking {description}: {e}")
        
        await asyncio.sleep(interval)
    
    print(f"Timeout waiting for {description} after {timeout} seconds")
    return False


def retry_on_failure(max_retries: int = 3, delay: float = 1.0, backoff: float = 2.0):
    """
    Decorator to retry function on failure
    
    Args:
        max_retries: Maximum number of retries
        delay: Initial delay between retries
        backoff: Backoff multiplier for delay
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            last_exception = None
            current_delay = delay
            
            for attempt in range(max_retries + 1):
                try:
                    if asyncio.iscoroutinefunction(func):
                        return await func(*args, **kwargs)
                    else:
                        return func(*args, **kwargs)
                except Exception as e:
                    last_exception = e
                    if attempt < max_retries:
                        print(f"Attempt {attempt + 1} failed: {e}. Retrying in {current_delay}s...")
                        await asyncio.sleep(current_delay)
                        current_delay *= backoff
                    else:
                        print(f"All {max_retries + 1} attempts failed")
            
            raise last_exception
        return wrapper
    return decorator


class DataManager:
    """Manage test data and cleanup"""
    
    def __init__(self):
        self.created_resources = []
    
    def track_resource(self, resource_type: str, resource_id: str, cleanup_func: Callable = None):
        """Track a created resource for cleanup"""
        self.created_resources.append({
            'type': resource_type,
            'id': resource_id,
            'cleanup_func': cleanup_func
        })
    
    async def cleanup_all(self):
        """Clean up all tracked resources"""
        for resource in reversed(self.created_resources):
            try:
                if resource['cleanup_func']:
                    if asyncio.iscoroutinefunction(resource['cleanup_func']):
                        await resource['cleanup_func'](resource['id'])
                    else:
                        resource['cleanup_func'](resource['id'])
                print(f"Cleaned up {resource['type']}: {resource['id']}")
            except Exception as e:
                print(f"Failed to cleanup {resource['type']} {resource['id']}: {e}")
        
        self.created_resources.clear()


def validate_response_schema(response: Dict[str, Any], required_fields: List[str], optional_fields: List[str] = None) -> bool:
    """
    Validate response schema
    
    Args:
        response: Response dictionary to validate
        required_fields: List of required field names
        optional_fields: List of optional field names
    
    Returns:
        True if schema is valid
    
    Raises:
        AssertionError: If schema validation fails
    """
    optional_fields = optional_fields or []
    
    # Check required fields
    missing_fields = [field for field in required_fields if field not in response]
    if missing_fields:
        raise AssertionError(f"Missing required fields: {missing_fields}")
    
    # Check for unexpected fields (optional validation)
    allowed_fields = set(required_fields + optional_fields)
    unexpected_fields = [field for field in response.keys() if field not in allowed_fields]
    if unexpected_fields:
        print(f"Warning: Unexpected fields found: {unexpected_fields}")
    
    return True


def generate_test_id(prefix: str = "test") -> str:
    """Generate unique test ID"""
    import uuid
    return f"{prefix}-{uuid.uuid4().hex[:8]}"


def load_test_data(filename: str) -> Dict[str, Any]:
    """Load test data from fixtures directory"""
    import os
    import json
    
    fixtures_dir = os.path.join(os.path.dirname(__file__), '..', 'fixtures')
    filepath = os.path.join(fixtures_dir, filename)
    
    with open(filepath, 'r') as f:
        return json.load(f)


def safe_json_loads(data: str) -> Optional[Dict[str, Any]]:
    """Safely load JSON data"""
    try:
        return json.loads(data)
    except (json.JSONDecodeError, TypeError):
        return None


def extract_nested_field(data: Dict[str, Any], field_path: str, default: Any = None) -> Any:
    """
    Extract nested field from dictionary using dot notation
    
    Args:
        data: Dictionary to extract from
        field_path: Dot-separated field path (e.g., 'user.profile.name')
        default: Default value if field not found
    
    Returns:
        Field value or default
    """
    try:
        value = data
        for key in field_path.split('.'):
            value = value[key]
        return value
    except (KeyError, TypeError):
        return default


def mask_sensitive_data(data: Dict[str, Any], sensitive_fields: List[str] = None) -> Dict[str, Any]:
    """
    Mask sensitive data in dictionary for logging
    
    Args:
        data: Dictionary to mask
        sensitive_fields: List of field names to mask
    
    Returns:
        Dictionary with sensitive fields masked
    """
    if sensitive_fields is None:
        sensitive_fields = ['password', 'secret', 'token', 'key', 'api_key']
    
    masked_data = data.copy()
    
    for field in sensitive_fields:
        if field in masked_data:
            masked_data[field] = "***MASKED***"
    
    return masked_data


def calculate_duration_ms(start_time: float, end_time: float) -> int:
    """Calculate duration in milliseconds"""
    return int((end_time - start_time) * 1000)


def is_valid_uuid(uuid_string: str) -> bool:
    """Check if string is valid UUID"""
    import uuid
    try:
        uuid.UUID(uuid_string)
        return True
    except ValueError:
        return False


def is_valid_iso_datetime(datetime_string: str) -> bool:
    """Check if string is valid ISO datetime"""
    from datetime import datetime
    try:
        datetime.fromisoformat(datetime_string.replace('Z', '+00:00'))
        return True
    except ValueError:
        return False


class TestMetrics:
    """Collect and track test metrics"""
    
    def __init__(self):
        self.metrics = {}
        self.start_times = {}
    
    def start_timer(self, name: str):
        """Start timing an operation"""
        self.start_times[name] = time.time()
    
    def end_timer(self, name: str) -> float:
        """End timing and return duration"""
        if name in self.start_times:
            duration = time.time() - self.start_times[name]
            self.metrics[f"{name}_duration"] = duration
            del self.start_times[name]
            return duration
        return 0.0
    
    def increment_counter(self, name: str, value: int = 1):
        """Increment a counter metric"""
        self.metrics[name] = self.metrics.get(name, 0) + value
    
    def set_gauge(self, name: str, value: float):
        """Set a gauge metric"""
        self.metrics[name] = value
    
    def get_metrics(self) -> Dict[str, Any]:
        """Get all collected metrics"""
        return self.metrics.copy()
    
    def reset(self):
        """Reset all metrics"""
        self.metrics.clear()
        self.start_times.clear()
