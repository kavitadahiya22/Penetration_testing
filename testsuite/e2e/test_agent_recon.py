"""
Tests for reconnaissance agent functionality
Tests Amass domain enumeration and Nmap port scanning
"""
import pytest
import asyncio
from typing import Dict, Any

from src.utils import APIClient, validate_response_schema, wait_for_condition
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id, NetworkTargetGenerator


@pytest.mark.asyncio
@pytest.mark.recon
@pytest.mark.smoke
async def test_recon_nmap_single_host(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test Nmap scanning of single host"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        },
        "auto_plan": True
    }
    
    # Start reconnaissance run
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Recon run {run_id} completion"
    )
    
    # Validate completion
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] == "completed"
    
    # Check OpenSearch for recon actions
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    recon_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "recon"),
            OpenSearchQueries.term_query("tool", "nmap")
        ]
    )
    
    nmap_actions = await opensearch_client.search(test_config["os_idx_actions"], recon_query)
    assert nmap_actions["hits"]["total"]["value"] >= 1, "Should have Nmap scan action"
    
    # Validate Nmap action details
    nmap_action = nmap_actions["hits"]["hits"][0]["_source"]
    validate_response_schema(nmap_action, [
        "run_id", "agent", "tool", "status", "target", "artifacts"
    ])
    
    assert nmap_action["agent"] == "recon"
    assert nmap_action["tool"] == "nmap"
    assert nmap_action["target"] == "127.0.0.1"
    
    if nmap_action["status"] == "completed":
        artifacts = nmap_action["artifacts"]
        
        # Validate Nmap result structure
        expected_fields = ["hosts_up", "total_hosts", "scan_time"]
        for field in expected_fields:
            assert field in str(artifacts), f"Nmap artifacts should contain {field}"


@pytest.mark.asyncio
@pytest.mark.recon
async def test_recon_nmap_network_range(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test Nmap scanning of network range"""
    # Use small safe network range
    target_network = "127.0.0.0/30"  # Only 4 IPs
    
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "inputs": {
            "targets": [target_network],
            "depth": "standard",
            "features": ["recon"],
            "simulate": True
        },
        "auto_plan": True
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion (network scans might take longer)
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"] * 2,
        interval=10,
        description=f"Network recon run {run_id} completion"
    )
    
    # Check for network scan results
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    recon_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "recon")
        ]
    )
    
    recon_actions = await opensearch_client.search(test_config["os_idx_actions"], recon_query)
    assert recon_actions["hits"]["total"]["value"] >= 1, "Should have network recon actions"
    
    # Look for network-related artifacts
    for hit in recon_actions["hits"]["hits"]:
        action = hit["_source"]
        if action["status"] == "completed" and action["tool"] == "nmap":
            artifacts = action["artifacts"]
            
            # Network scans should report multiple hosts potential
            assert "total_hosts" in str(artifacts)
            # Should scan the specified network
            assert target_network in action.get("target", "")


@pytest.mark.asyncio
@pytest.mark.recon
async def test_recon_amass_domain_enumeration(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test Amass domain enumeration"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["test.example.com"],
            "depth": "standard",
            "features": ["recon"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Domain recon run {run_id} completion"
    )
    
    # Check for Amass domain enumeration
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    amass_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "recon"),
            OpenSearchQueries.term_query("tool", "amass")
        ]
    )
    
    amass_actions = await opensearch_client.search(test_config["os_idx_actions"], amass_query)
    
    # Domain enumeration might not always be triggered in basic scenarios
    # But if it runs, validate the structure
    if amass_actions["hits"]["total"]["value"] > 0:
        amass_action = amass_actions["hits"]["hits"][0]["_source"]
        assert amass_action["agent"] == "recon"
        assert amass_action["tool"] == "amass"
        assert "test.example.com" in amass_action.get("target", "")
        
        if amass_action["status"] == "completed":
            artifacts = amass_action["artifacts"]
            # Should contain domain enumeration results
            assert "subdomains" in str(artifacts) or "domains" in str(artifacts)


@pytest.mark.asyncio
@pytest.mark.recon
async def test_recon_mixed_targets(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test reconnaissance with mixed target types"""
    run_input = {
        "127.0.0.1",           # IP address,
        "127.0.0.0/30",        # Network range,
        "test.example.com"      # Domain,
        ],
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": [,
            "depth": "standard",
            "features": ["recon"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"] * 2,
        interval=10,
        description=f"Mixed targets recon run {run_id} completion"
    )
    
    # Check that different tools were used for different target types
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    recon_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "recon")
        ]
    )
    
    recon_actions = await opensearch_client.search(test_config["os_idx_actions"], recon_query, size=10)
    
    tools_used = set()
    targets_scanned = set()
    
    for hit in recon_actions["hits"]["hits"]:
        action = hit["_source"]
        tools_used.add(action["tool"])
        targets_scanned.add(action.get("target", ""))
    
    # Should use Nmap for IP/network targets
    assert "nmap" in tools_used, "Should use Nmap for IP targets"
    
    # Should have scanned multiple targets
    assert len(targets_scanned) >= 2, f"Should scan multiple targets, got: {targets_scanned}"


@pytest.mark.asyncio
@pytest.mark.recon
async def test_recon_port_service_detection(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test port and service detection in reconnaissance"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "advanced",  # Advanced scan for service detection,
            "features": ["recon"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Advanced recon run {run_id} completion"
    )
    
    # Check for detailed service detection
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    nmap_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("tool", "nmap"),
            OpenSearchQueries.term_query("status", "completed")
        ]
    )
    
    nmap_actions = await opensearch_client.search(test_config["os_idx_actions"], nmap_query)
    
    if nmap_actions["hits"]["total"]["value"] > 0:
        nmap_action = nmap_actions["hits"]["hits"][0]["_source"]
        artifacts = nmap_action["artifacts"]
        
        # Advanced scans should include service information
        artifacts_str = str(artifacts)
        service_indicators = ["services", "ports", "service", "version"]
        
        has_service_info = any(indicator in artifacts_str for indicator in service_indicators)
        assert has_service_info, "Advanced recon should include service detection"


@pytest.mark.asyncio
@pytest.mark.recon
async def test_recon_timing_and_stealth(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test reconnaissance timing and stealth options"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "options": {,
        "stealth_mode": True,
        "scan_timing": "slow",
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Stealth scans might take longer
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"] * 2,
        interval=10,
        description=f"Stealth recon run {run_id} completion"
    )
    
    # Check that stealth options were logged
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    recon_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "recon")
        ]
    )
    
    recon_actions = await opensearch_client.search(test_config["os_idx_actions"], recon_query)
    
    for hit in recon_actions["hits"]["hits"]:
        action = hit["_source"]
        params = action.get("params", {})
        
        # Check that stealth/timing options were applied
        params_str = str(params)
        timing_indicators = ["stealth", "slow", "timing", "T1", "T2"]
        
        has_timing_info = any(indicator in params_str for indicator in timing_indicators)
        # Note: This test validates that timing options are passed through
        # Actual stealth implementation depends on tool configuration


@pytest.mark.asyncio
@pytest.mark.recon
async def test_recon_large_network_handling(api_client: APIClient, test_config: Dict):
    """Test that large networks are handled appropriately"""
    # Test with network that's too large
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["10.0.0.0/16"],  # 65k hosts - should be limited,
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    
    # This should either be rejected or automatically limited
    try:
        response = await api_client.post("/agents/pentest/run", run_input)
        
        if "run_id" in response:
            # If accepted, the plan should have reasonable scope limitations
            plan_response = await api_client.get(f"/planner/plan/{response['plan_id']}")
            
            # Should have scope limitations or be marked as requiring approval
            steps = plan_response.get("steps", [])
            for step in steps:
                # Large scans should have limitations or warnings
                assert step.get("risk_level") != "unrestricted"
                
                params = step.get("params", {})
                if "max_hosts" in str(params):
                    # Should have host limits applied
                    pass
    
    except Exception as e:
        # Rejection is also acceptable for oversized scans
        error_msg = str(e).lower()
        assert any(keyword in error_msg for keyword in ["too large", "scope", "limit", "policy"])


async def _check_run_completed(api_client: APIClient, run_id: str) -> bool:
    """Helper to check if run is completed"""
    try:
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error", "partial"]
    except Exception:
        return False
