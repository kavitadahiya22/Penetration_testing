"""
Optimized HTTP Client Configuration for Pentest Operations
Addresses timeout issues identified in SET report
"""

import httpx
from typing import Optional

class OptimizedAPIClient:
    """API client with optimized timeout settings for pentest operations"""
    
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip('/')
        
        # Optimized timeout configuration for pentest operations
        timeout_config = httpx.Timeout(
            connect=30.0,    # Connection establishment timeout
            read=300.0,      # Read timeout - increased for long pentest operations  
            write=30.0,      # Write timeout
            pool=10.0        # Connection pool timeout
        )
        
        # Connection limits to prevent resource exhaustion
        limits_config = httpx.Limits(
            max_keepalive_connections=10,
            max_connections=20
        )
        
        self.client = httpx.AsyncClient(
            timeout=timeout_config,
            limits=limits_config,
            headers={
                "Content-Type": "application/json",
                "Accept": "application/json"
            }
        )
    
    async def post(self, endpoint: str, data: dict) -> dict:
        """POST request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.post(url, json=data)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Request timeout for {endpoint} - operation may be long-running")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
    
    async def get(self, endpoint: str) -> dict:
        """GET request with error handling"""
        url = f"{self.base_url}{endpoint}"
        try:
            response = await self.client.get(url)
            response.raise_for_status()
            return response.json()
        except httpx.TimeoutException:
            raise Exception(f"Request timeout for {endpoint}")
        except httpx.HTTPStatusError as e:
            raise Exception(f"HTTP {e.response.status_code}: {e.response.text}")
    
    async def close(self):
        """Close the HTTP client"""
        await self.client.aclose()

# Usage in tests:
# from timeout_config import OptimizedAPIClient
# api_client = OptimizedAPIClient(test_config["api_base"])
