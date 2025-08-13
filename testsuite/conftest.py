"""
Test configuration and fixtures for cybrty-pentest test suite
"""
import pytest
import pytest_asyncio
import os
import asyncio
from typing import Dict, Any, AsyncGenerator
from src.utils import APIClient, wait_for_condition
from src.os_queries import OpenSearchClient


def pytest_configure(config):
    """Configure pytest with custom markers"""
    config.addinivalue_line("markers", "smoke: quick smoke tests")
    config.addinivalue_line("markers", "recon: reconnaissance agent tests")
    config.addinivalue_line("markers", "web: web application tests") 
    config.addinivalue_line("markers", "exploit: exploitation tests")
    config.addinivalue_line("markers", "creds: credential testing")
    config.addinivalue_line("markers", "lateral: lateral movement tests")
    config.addinivalue_line("markers", "privesc: privilege escalation tests")
    config.addinivalue_line("markers", "planner: dynamic planning tests")
    config.addinivalue_line("markers", "logging: OpenSearch logging tests")
    config.addinivalue_line("markers", "policy: policy and safety tests")
    config.addinivalue_line("markers", "safety: safety and security tests")
    config.addinivalue_line("markers", "negative: negative/edge case tests")
    config.addinivalue_line("markers", "performance: performance tests")
    config.addinivalue_line("markers", "integration: integration tests")


@pytest.fixture(scope="session")
def event_loop():
    """Create an instance of the default event loop for the test session."""
    loop = asyncio.get_event_loop_policy().new_event_loop()
    yield loop
    loop.close()


@pytest.fixture(scope="session")
def test_config() -> Dict[str, Any]:
    """Load test configuration from environment"""
    return {
        "api_base": os.getenv("API_BASE", "http://localhost:8080/api/v1"),
        "api_timeout": int(os.getenv("API_TIMEOUT", "30")),
        "os_host": os.getenv("OS_HOST", "localhost"),
        "os_port": int(os.getenv("OS_PORT", "9200")),
        "os_scheme": os.getenv("OS_SCHEME", "http"),
        "os_username": os.getenv("OS_USERNAME", ""),
        "os_password": os.getenv("OS_PASSWORD", ""),
        "os_verify_certs": os.getenv("OS_VERIFY_CERTS", "false").lower() == "true",
        "os_timeout": int(os.getenv("OS_TIMEOUT", "30")),
        "os_idx_planner": os.getenv("OS_IDX_PLANNER", "cybrty-planner"),
        "os_idx_actions": os.getenv("OS_IDX_ACTIONS", "cybrty-actions"),
        "os_idx_runs": os.getenv("OS_IDX_RUNS", "cybrty-runs"),
        "tenant_id": os.getenv("DEFAULT_TENANT_ID", "test-tenant-001"),
        "test_timeout": int(os.getenv("TEST_TIMEOUT", "300")),
        "simulate": os.getenv("DEFAULT_SIMULATE", "true").lower() == "true",
        "use_mocks": os.getenv("USE_MOCKS", "true").lower() == "true",
        "model_provider": os.getenv("MODEL_PROVIDER", "ollama"),
        "ollama_url": os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    }


@pytest_asyncio.fixture(scope="function")
async def api_client(test_config) -> AsyncGenerator[APIClient, None]:
    """Create API client for testing"""
    client = APIClient(
        base_url=test_config["api_base"],
        timeout=test_config["api_timeout"]
    )
    
    # Wait for API to be ready
    await wait_for_condition(
        client.health_check,
        timeout=60,
        interval=2,
        description="API health check"
    )
    
    yield client
    await client.close()


@pytest_asyncio.fixture(scope="function")
async def opensearch_client(test_config) -> AsyncGenerator[OpenSearchClient, None]:
    """Create OpenSearch client for testing"""
    client = OpenSearchClient(
        host=test_config["os_host"],
        port=test_config["os_port"],
        scheme=test_config["os_scheme"],
        username=test_config["os_username"],
        password=test_config["os_password"],
        verify_certs=test_config["os_verify_certs"],
        timeout=test_config["os_timeout"]
    )
    
    # Wait for OpenSearch to be ready
    await wait_for_condition(
        client.cluster_health,
        timeout=60,
        interval=2,
        description="OpenSearch cluster health"
    )
    
    yield client
    await client.close()


@pytest.fixture
def sample_planner_input(test_config):
    """Sample input for planner tests"""
    return {
        "targets": ["127.0.0.1/32"],
        "depth": "basic",
        "features": ["recon"],
        "simulate": test_config["simulate"],
        "tenant_id": test_config["tenant_id"]
    }


@pytest.fixture
def sample_web_targets():
    """Sample web targets for testing"""
    return [
        "http://test-target/",
        "http://127.0.0.1:8092/",
        "http://httpbin.org/get"
    ]


@pytest.fixture
def sample_network_targets():
    """Sample network targets for testing"""
    return [
        "127.0.0.1",
        "127.0.0.1/32",
        "10.0.1.1"
    ]


@pytest.fixture
def bloodhound_sample_data():
    """Sample BloodHound data for testing"""
    import json
    with open("data/bloodhound/sample_domain.json", "r") as f:
        return json.load(f)


@pytest.fixture
def test_credentials():
    """Sample credentials for testing"""
    return [
        {"username": "admin", "password": "admin", "service": "http"},
        {"username": "test", "password": "test", "service": "ssh"},
        {"username": "user", "password": "password", "service": "ftp"}
    ]


@pytest_asyncio.fixture(autouse=True)
async def cleanup_test_data(opensearch_client, test_config):
    """Clean up test data after each test (optional)"""
    yield
    
    # Only cleanup if not preserving test data
    if not os.getenv("PRESERVE_TEST_DATA", "false").lower() == "true":
        # Clean up test indices if needed
        pass


@pytest.fixture
def mock_tool_responses():
    """Mock responses for external tools"""
    return {
        "nmap": {
            "hosts_up": 1,
            "total_hosts": 1,
            "scan_time": 10.5,
            "services": [
                {"port": 22, "service": "ssh", "state": "open"},
                {"port": 80, "service": "http", "state": "open"}
            ]
        },
        "zap_baseline": {
            "scan_id": "test-scan-001",
            "status": "completed",
            "alerts": [
                {
                    "name": "X-Content-Type-Options Header Missing",
                    "risk": "Low",
                    "confidence": "Medium"
                }
            ],
            "summary": {"high": 0, "medium": 0, "low": 1, "total": 1}
        },
        "metasploit": {
            "exploit_id": "test-exploit-001",
            "status": "simulated",
            "result": "simulation_only",
            "vulnerable": True,
            "confidence": 0.85
        }
    }


# Session-scoped fixtures for expensive setup
@pytest.fixture(scope="session")
def test_environment_ready(test_config):
    """Ensure test environment is ready"""
    import requests
    import time
    
    # Check if API is responding
    max_retries = 30
    for _ in range(max_retries):
        try:
            response = requests.get(f"{test_config['api_base'].replace('/api/v1', '')}/health", timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(2)
    else:
        pytest.fail("Test environment not ready - API not responding")
    
    # Check if OpenSearch is responding
    for _ in range(max_retries):
        try:
            url = f"{test_config['os_scheme']}://{test_config['os_host']}:{test_config['os_port']}/_cluster/health"
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                break
        except:
            pass
        time.sleep(2)
    else:
        pytest.fail("Test environment not ready - OpenSearch not responding")
    
    return True
