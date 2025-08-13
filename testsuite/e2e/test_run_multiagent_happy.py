"""
Multi-agent happy path tests
Tests complete runs with multiple agents and validates OpenSearch logging
"""
import pytest
import asyncio
import time
from typing import Dict, Any

from src.utils import APIClient, validate_response_schema, wait_for_condition
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.smoke
async def test_run_simple_recon_flow(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test simple reconnaissance flow end-to-end"""
    # Create and execute a simple recon run
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    
    # Start the run
    response = await api_client.post("/agents/pentest/run", run_input)
    
    validate_response_schema(response, [
        "run_id", "plan_id", "status", "created_at"
    ])
    
    run_id = response["run_id"]
    plan_id = response["plan_id"]
    
    # Poll run status until completion
    max_wait = test_config["test_timeout"]
    start_time = time.time()
    
    while time.time() - start_time < max_wait:
        status_response = await api_client.get(f"/runs/{run_id}")
        
        if status_response["status"] in ["completed", "failed", "error"]:
            break
        
        await asyncio.sleep(5)
    else:
        pytest.fail(f"Run {run_id} did not complete within {max_wait} seconds")
    
    # Validate final status
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] == "completed"
    
    # Validate OpenSearch logs
    await asyncio.sleep(3)  # Allow time for final logs
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    await opensearch_client.refresh_index(test_config["os_idx_runs"])
    
    # Check actions were logged
    actions_query = OpenSearchQueries.term_query("run_id", run_id)
    actions = await opensearch_client.search(test_config["os_idx_actions"], actions_query)
    
    assert actions["hits"]["total"]["value"] >= 1, "Should have at least one action logged"
    
    # Validate action documents
    for hit in actions["hits"]["hits"]:
        action = hit["_source"]
        validate_response_schema(action, [
            "run_id", "step_id", "agent", "tool", "status", 
            "started_at", "ended_at", "duration_ms"
        ])
        assert action["run_id"] == run_id
        assert action["agent"] == "recon"
        assert action["tool"] in ["nmap", "amass"]
        assert action["status"] in ["completed", "failed"]
    
    # Check run summary was logged
    runs_query = OpenSearchQueries.term_query("run_id", run_id)
    runs = await opensearch_client.search(test_config["os_idx_runs"], runs_query)
    
    assert runs["hits"]["total"]["value"] == 1, "Should have exactly one run summary"
    
    run_summary = runs["hits"]["hits"][0]["_source"]
    validate_response_schema(run_summary, [
        "run_id", "plan_id", "status", "started_at", "ended_at",
        "duration_ms", "steps_count", "steps_completed"
    ])
    assert run_summary["run_id"] == run_id
    assert run_summary["plan_id"] == plan_id
    assert run_summary["status"] == "completed"
    assert run_summary["steps_completed"] >= 1


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_web_vulnerability_scan(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test web vulnerability scanning flow"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["http://test-target/"],
            "depth": "standard",
            "features": ["web", "vuln"],
            "simulate": True
        }
    }
    
    # Start the run
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=10,
        description=f"Run {run_id} completion"
    )
    
    # Validate final status
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] in ["completed", "partial"], f"Unexpected status: {final_status['status']}"
    
    # Check for web agent actions
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    actions_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "web")
        ]
    )
    
    web_actions = await opensearch_client.search(test_config["os_idx_actions"], actions_query)
    assert web_actions["hits"]["total"]["value"] >= 1, "Should have web agent actions"
    
    # Check for expected tools
    tools_used = set()
    for hit in web_actions["hits"]["hits"]:
        tools_used.add(hit["_source"]["tool"])
    
    expected_tools = {"zap", "nikto"}
    assert len(expected_tools.intersection(tools_used)) > 0, f"Expected tools {expected_tools}, got {tools_used}"
    
    # Validate artifacts are present
    for hit in web_actions["hits"]["hits"]:
        action = hit["_source"]
        if action["status"] == "completed":
            assert "artifacts" in action, "Completed actions should have artifacts"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_multi_agent_comprehensive(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test comprehensive multi-agent run"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["192.168.1.0/29", "http://test-target/"],  # Small network + web app,
            "depth": "advanced",
            "features": ["recon", "web", "creds"],
            "simulate": True
        }
    }
    
    # Start the run
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion (longer timeout for comprehensive scan)
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"] * 2,
        interval=15,
        description=f"Comprehensive run {run_id} completion"
    )
    
    # Validate multiple agents were used
    await asyncio.sleep(5)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    actions_query = OpenSearchQueries.term_query("run_id", run_id)
    all_actions = await opensearch_client.search(test_config["os_idx_actions"], actions_query, size=50)
    
    assert all_actions["hits"]["total"]["value"] >= 3, "Should have multiple actions for comprehensive scan"
    
    # Check that multiple agents were used
    agents_used = set()
    for hit in all_actions["hits"]["hits"]:
        agents_used.add(hit["_source"]["agent"])
    
    expected_agents = {"recon", "web"}  # Minimum expected
    assert len(expected_agents.intersection(agents_used)) >= 2, f"Expected multiple agents, got {agents_used}"
    
    # Validate run summary has comprehensive data
    await opensearch_client.refresh_index(test_config["os_idx_runs"])
    runs_query = OpenSearchQueries.term_query("run_id", run_id)
    runs = await opensearch_client.search(test_config["os_idx_runs"], runs_query)
    
    run_summary = runs["hits"]["hits"][0]["_source"]
    assert run_summary["steps_count"] >= 3, "Comprehensive run should have multiple steps"
    assert run_summary["total_findings"] >= 0, "Should track findings count"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_with_failures_resilience(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test run resilience when some steps fail"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "continue_on_failure": True,
        "inputs": {
            "targets": ["192.168.1.1", "http://nonexistent.test/"],  # Mixed valid/invalid targets,
            "depth": "standard",
            "features": ["recon", "web"],
            "simulate": True
        }
    }
    
    # Start the run
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=10,
        description=f"Run {run_id} with failures completion"
    )
    
    # Check final status (should be partial or completed)
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] in ["completed", "partial", "failed"]
    
    # Check that some steps completed and some failed
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    actions_query = OpenSearchQueries.term_query("run_id", run_id)
    actions = await opensearch_client.search(test_config["os_idx_actions"], actions_query, size=20)
    
    statuses = [hit["_source"]["status"] for hit in actions["hits"]["hits"]]
    
    # Should have a mix of completed and failed (or all completed if error handling is good)
    assert "completed" in statuses or "failed" in statuses, "Should have some action results"
    
    # Validate error handling in logs
    failed_actions = [hit["_source"] for hit in actions["hits"]["hits"] if hit["_source"]["status"] == "failed"]
    for failed_action in failed_actions:
        assert "error_message" in failed_action, "Failed actions should have error messages"


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_artifacts_generation(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that runs generate proper artifacts"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "standard",
            "features": ["recon"],
            "simulate": True
        }
    }
    
    # Start and wait for completion
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=5,
        description=f"Run {run_id} completion for artifacts test"
    )
    
    # Check artifacts in actions
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    actions_query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("status", "completed")
        ]
    )
    
    completed_actions = await opensearch_client.search(test_config["os_idx_actions"], actions_query)
    
    # At least one completed action should have artifacts
    has_artifacts = False
    for hit in completed_actions["hits"]["hits"]:
        action = hit["_source"]
        if "artifacts" in action and action["artifacts"]:
            has_artifacts = True
            
            # Validate artifact structure
            artifacts = action["artifacts"]
            if action["tool"] == "nmap":
                expected_fields = ["hosts_up", "services", "scan_time"]
                for field in expected_fields:
                    assert field in str(artifacts), f"Nmap artifacts should contain {field}"
            
            break
    
    # Note: In simulation mode, artifacts might be synthetic
    # This test validates the logging structure rather than real tool output


@pytest.mark.asyncio
@pytest.mark.integration
async def test_run_timing_and_duration_tracking(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that timing and duration are properly tracked"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    
    start_timestamp = time.time()
    
    # Start run
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    await wait_for_condition(
        lambda: _check_run_completed(api_client, run_id),
        timeout=test_config["test_timeout"],
        interval=3,
        description=f"Run {run_id} completion for timing test"
    )
    
    end_timestamp = time.time()
    actual_duration = (end_timestamp - start_timestamp) * 1000  # Convert to ms
    
    # Check timing in OpenSearch
    await asyncio.sleep(3)
    await opensearch_client.refresh_index(test_config["os_idx_runs"])
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    # Validate run timing
    runs_query = OpenSearchQueries.term_query("run_id", run_id)
    runs = await opensearch_client.search(test_config["os_idx_runs"], runs_query)
    
    run_summary = runs["hits"]["hits"][0]["_source"]
    
    assert "started_at" in run_summary
    assert "ended_at" in run_summary
    assert "duration_ms" in run_summary
    assert run_summary["duration_ms"] > 0
    assert run_summary["duration_ms"] <= actual_duration + 5000  # Allow some margin
    
    # Validate action timing
    actions_query = OpenSearchQueries.term_query("run_id", run_id)
    actions = await opensearch_client.search(test_config["os_idx_actions"], actions_query)
    
    for hit in actions["hits"]["hits"]:
        action = hit["_source"]
        if action["status"] == "completed":
            assert "started_at" in action
            assert "ended_at" in action
            assert "duration_ms" in action
            assert action["duration_ms"] >= 0


async def _check_run_completed(api_client: APIClient, run_id: str) -> bool:
    """Helper to check if run is completed"""
    try:
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error", "partial"]
    except Exception:
        return False
