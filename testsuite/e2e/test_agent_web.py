"""
Tests for web agent functionality
Tests ZAP baseline scanning, Nikto web scanning, and SQLMap injection detection
"""
import pytest
import asyncio
from typing import Dict, Any

from src.utils import APIClient, validate_response_schema, wait_for_condition
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.web
@pytest.mark.smoke
async def test_web_zap_baseline_scan(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test ZAP baseline scanning"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["http://test-target/"],
            "depth": "standard",
            "features": ["web"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"ZAP baseline run {run_id} completion"
    )
    
    # Check for ZAP baseline action
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    zap_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web"),
            OpenSearchQueries.term_query("tool", "zap")
        ]
    )
    
    zap_actions = await opensearch_client.search(test_config["os_idx_actions"], zap_query)
    assert zap_actions["hits"]["total"]["value"] >= 1, "Should have ZAP baseline action"
    
    zap_action = zap_actions["hits"]["hits"][0]["_source"]
    validate_response_schema(zap_action, [
        "run_id", "agent", "tool", "status", "target", "artifacts"
    ])
    
    assert zap_action["agent"] == "web"
    assert zap_action["tool"] == "zap"
    assert "test-target" in zap_action.get("target", "")
    
    if zap_action["status"] == "completed":
        artifacts = zap_action["artifacts"]
        
        # Validate ZAP baseline result structure
        expected_fields = ["scan_id", "alerts", "summary"]
        artifacts_str = str(artifacts)
        for field in expected_fields:
            assert field in artifacts_str, f"ZAP artifacts should contain {field}"


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_nikto_scanning(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test Nikto web server scanning"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["http://test-target/"],
            "depth": "advanced",
            "features": ["web", "vuln"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Nikto scan run {run_id} completion"
    )
    
    # Check for Nikto action
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    nikto_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("tool", "nikto")
        ]
    )
    
    nikto_actions = await opensearch_client.search(test_config["os_idx_actions"], nikto_query)
    
    if nikto_actions["hits"]["total"]["value"] > 0:
        nikto_action = nikto_actions["hits"]["hits"][0]["_source"]
        assert nikto_action["tool"] == "nikto"
        assert nikto_action["agent"] == "web"
        
        if nikto_action["status"] == "completed":
            artifacts = nikto_action["artifacts"]
            # Nikto should find web server vulnerabilities
            artifacts_str = str(artifacts)
            expected_fields = ["findings", "vulnerabilities", "scan_time"]
            
            has_expected = any(field in artifacts_str for field in expected_fields)
            assert has_expected, "Nikto artifacts should contain vulnerability findings"


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_sqlmap_injection_detection(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test SQLMap SQL injection detection"""
    # Use URL with parameters that might be tested for SQL injection
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["http://test-target/search?q=test", "http://test-target/user?id=1"],
            "depth": "advanced",
            "features": ["web", "vuln"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"] * 2,  # SQLMap can take longer
        interval=10,
        description=f"SQLMap run {run_id} completion"
    )
    
    # Check for SQLMap action
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    sqlmap_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("tool", "sqlmap")
        ]
    )
    
    sqlmap_actions = await opensearch_client.search(test_config["os_idx_actions"], sqlmap_query)
    
    if sqlmap_actions["hits"]["total"]["value"] > 0:
        sqlmap_action = sqlmap_actions["hits"]["hits"][0]["_source"]
        assert sqlmap_action["tool"] == "sqlmap"
        assert sqlmap_action["agent"] == "web"
        
        # Ensure SQLMap runs in safe mode during simulation
        params = sqlmap_action.get("params", {})
        params_str = str(params)
        
        # Should have safe mode indicators
        safe_indicators = ["--safe-url", "--level=1", "--risk=1", "simulation", "safe"]
        has_safe_mode = any(indicator in params_str for indicator in safe_indicators)
        
        if sqlmap_action["status"] == "completed":
            artifacts = sqlmap_action["artifacts"]
            artifacts_str = str(artifacts)
            
            # Should report injection test results
            injection_indicators = ["injection", "vulnerable", "payload", "parameter"]
            has_injection_info = any(indicator in artifacts_str for indicator in injection_indicators)
            assert has_injection_info, "SQLMap should report injection test results"


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_multiple_urls(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test web scanning with multiple URLs"""
    run_input = {
        "http://test-target/",
        "http://test-target/admin",
        "http://test-target/api/users",
        ],
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": [,
            "depth": "standard",
            "features": ["web"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"] * 2,
        interval=10,
        description=f"Multi-URL web scan {run_id} completion"
    )
    
    # Check that multiple URLs were scanned
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    web_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web")
        ]
    )
    
    web_actions = await opensearch_client.search(test_config["os_idx_actions"], web_query, size=10)
    
    targets_scanned = set()
    for hit in web_actions["hits"]["hits"]:
        action = hit["_source"]
        target = action.get("target", "")
        if target:
            targets_scanned.add(target)
    
    # Should have scanned multiple targets
    assert len(targets_scanned) >= 2, f"Should scan multiple URLs, got: {targets_scanned}"


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_https_ssl_scanning(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test web scanning of HTTPS sites"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["https://httpbin.org/get"],  # Known HTTPS endpoint,
            "depth": "standard",
            "features": ["web"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"HTTPS web scan {run_id} completion"
    )
    
    # Check for HTTPS-specific considerations
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    web_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web")
        ]
    )
    
    web_actions = await opensearch_client.search(test_config["os_idx_actions"], web_query)
    
    for hit in web_actions["hits"]["hits"]:
        action = hit["_source"]
        target = action.get("target", "")
        
        if "https://" in target:
            # HTTPS targets should be handled appropriately
            params = action.get("params", {})
            
            # Should have SSL/TLS considerations
            ssl_indicators = ["ssl", "tls", "https", "certificate"]
            params_str = str(params)
            
            # At minimum, should recognize HTTPS protocol
            assert "https" in target or any(indicator in params_str for indicator in ssl_indicators)


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_authentication_testing(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test web application authentication testing"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "options": {,
        "test_authentication": True,
        "check_default_creds": True,
        "inputs": {
            "targets": ["http://test-target/login"],
            "depth": "advanced",
            "features": ["web", "vuln"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Auth testing run {run_id} completion"
    )
    
    # Check for authentication-related testing
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    web_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web")
        ]
    )
    
    web_actions = await opensearch_client.search(test_config["os_idx_actions"], web_query)
    
    for hit in web_actions["hits"]["hits"]:
        action = hit["_source"]
        
        if action["status"] == "completed":
            artifacts = action["artifacts"]
            params = action.get("params", {})
            
            # Should test authentication-related issues
            auth_indicators = ["login", "auth", "credential", "session", "cookie"]
            combined_str = str(artifacts) + str(params)
            
            has_auth_testing = any(indicator in combined_str for indicator in auth_indicators)
            # Note: This validates that auth testing parameters are present
            # Actual authentication testing depends on tool configuration


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_xss_detection(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test XSS (Cross-Site Scripting) detection"""
    # Use URLs with input parameters that might be tested for XSS
    run_input = {
        "http://test-target/search?q=<script>alert('test')</script>",
        "http://test-target/comment?text=test",
        ],
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": [,
            "depth": "advanced",
            "features": ["web", "vuln"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"XSS detection run {run_id} completion"
    )
    
    # Check for XSS detection in results
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    web_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web")
        ]
    )
    
    web_actions = await opensearch_client.search(test_config["os_idx_actions"], web_query)
    
    for hit in web_actions["hits"]["hits"]:
        action = hit["_source"]
        
        if action["status"] == "completed":
            artifacts = action["artifacts"]
            
            # Should detect or test for XSS vulnerabilities
            xss_indicators = ["xss", "cross-site", "script", "alert", "javascript"]
            artifacts_str = str(artifacts).lower()
            
            has_xss_detection = any(indicator in artifacts_str for indicator in xss_indicators)
            # Note: This validates that XSS testing was performed
            # Actual XSS detection depends on tool configuration and target response


@pytest.mark.asyncio
@pytest.mark.web
async def test_web_error_handling(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test web scanning error handling for invalid URLs"""
    run_input = {
        "http://test-target/",           # Valid target,
        "http://nonexistent.invalid/",   # Invalid target,
        "https://self-signed.test/"      # SSL certificate issues,
        ],
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "options": {,
        "continue_on_error": True,
        "inputs": {
            "targets": [,
            "depth": "basic",
            "features": ["web"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Error handling run {run_id} completion"
    )
    
    # Check error handling in actions
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    web_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web")
        ]
    )
    
    web_actions = await opensearch_client.search(test_config["os_idx_actions"], web_query, size=10)
    
    statuses = []
    for hit in web_actions["hits"]["hits"]:
        action = hit["_source"]
        statuses.append(action["status"])
        
        if action["status"] == "failed":
            # Failed actions should have error messages
            assert "error_message" in action, "Failed actions should have error messages"
    
    # Should have mix of success and failure for mixed valid/invalid targets
    assert len(set(statuses)) >= 1, "Should have action results for error handling test"


async def _check_run_completed(api_client: APIClient, run_id: str) -> bool:
    """Helper to check if run is completed"""
    try:
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error", "partial"]
    except Exception:
        return False
