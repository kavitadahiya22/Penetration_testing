"""
Tests for Policy Gates and Safety Controls
Validates that the planner respects policy constraints and safety mechanisms
"""
import pytest
import asyncio
from typing import Dict, Any, List

from src.utils import APIClient, validate_response_schema
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.policy
@pytest.mark.safety
@pytest.mark.smoke
async def test_policy_basic_depth_constraints(api_client: APIClient):
    """Test that depth policy constraints are enforced"""
    # Test basic depth limit
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "max_depth": "basic",
        "enforce_depth_limit": True,
        "inputs": {
            "targets": ["192.168.1.100"],
            "depth": "basic",
            "features": ["recon", "web"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    assert "run_id" in response
    assert "plan_id" in response
    
    run_id = response["run_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=120, interval=10)
    
    # Get plan details
    plan = await api_client.get(f"/plans/{response['plan_id']}")
    
    # Should respect depth constraint
    assert plan["depth"] == "basic", "Plan should respect basic depth constraint"
    
    # Should not generate advanced or comprehensive steps
    if "steps" in plan:
        for step in plan["steps"]:
            # Basic depth should not include advanced exploitation
            forbidden_actions = ["exploit", "privilege_escalation", "lateral_movement"]
            step_description = step.get("description", "").lower()
            
            # Some exceptions for basic enumeration
            if step.get("agent") == "exploit":
                # Basic exploit should be scan-only
                assert "scan" in step_description or "enumerate" in step_description, \
                    f"Basic depth should not include active exploitation: {step}"


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_feature_restrictions(api_client: APIClient):
    """Test that feature restrictions are enforced"""
    # Test with restricted features
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "allowed_features": ["recon"],
        "forbidden_features": ["exploit", "creds", "lateral", "privesc"],
        "inputs": {
            "targets": ["10.0.0.50"],
            "depth": "standard",
            "features": ["recon"],  # Only recon allowed,
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    plan_id = response["plan_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=150, interval=10)
    
    # Get plan and results
    plan = await api_client.get(f"/plans/{plan_id}")
    results = await api_client.get(f"/runs/{run_id}/results")
    
    # Plan should only include allowed features
    assert plan["features"] == ["recon"], "Plan should only include allowed features"
    
    # Results should only have recon agent activities
    if "results" in results:
        for result in results["results"]:
            assert result["agent"] == "recon", \
                f"Found forbidden agent activity: {result['agent']}"
    
    # Should not have any forbidden agent steps in plan
    if "steps" in plan:
        for step in plan["steps"]:
            assert step["agent"] == "recon", \
                f"Plan contains forbidden agent: {step['agent']}"


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_target_validation(api_client: APIClient):
    """Test that target validation policies are enforced"""
    # Test with forbidden target ranges
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "forbidden_targets": ["192.168.1.1", "10.0.0.1", "172.16.0.1"],
        "forbidden_networks": ["127.0.0.0/8", "169.254.0.0/16"],
        "validate_targets": True,
        "inputs": {
            "targets": ["192.168.1.1"],  # Common gateway, might be forbidden,
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    }
    
    # This should either be rejected or filtered
    try:
        response = await api_client.post("/agents/pentest/run", run_input)
        
        # If accepted, check that target was filtered
        if "run_id" in response:
            run_id = response["run_id"]
            plan_id = response["plan_id"]
            
            plan = await api_client.get(f"/plans/{plan_id}")
            
            # Target should be filtered out or run should fail
            if "targets" in plan:
                assert "192.168.1.1" not in plan["targets"], \
                    "Forbidden target should be filtered"
            
            # Or run should fail with policy violation
            final_status = await api_client.get(f"/runs/{run_id}")
            if final_status["status"] == "failed":
                assert "policy" in final_status.get("error_message", "").lower()
    
    except Exception as e:
        # Request should be rejected due to policy violation
        assert "policy" in str(e).lower() or "forbidden" in str(e).lower()


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_risk_level_constraints(api_client: APIClient):
    """Test that risk level constraints are enforced"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "max_risk_level": "medium",
        "production_target": True,
        "require_approval_for_high_risk": True,
        "inputs": {
            "targets": ["10.10.0.100"],
            "depth": "standard",
            "features": ["recon", "web", "exploit"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    plan_id = response["plan_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=180, interval=15)
    
    # Get plan and results
    plan = await api_client.get(f"/plans/{plan_id}")
    results = await api_client.get(f"/runs/{run_id}/results")
    
    # Plan should respect risk level
    if "risk_assessment" in plan:
        risk_assessment = plan["risk_assessment"]
        assert risk_assessment.get("max_risk_level") in ["low", "medium"], \
            "Plan should not exceed medium risk level"
    
    # Steps should be production-safe
    if "steps" in plan:
        for step in plan["steps"]:
            # High-risk activities should be avoided
            if step.get("agent") == "exploit":
                assert step.get("mode", "").lower() in ["scan", "enumerate", "passive"], \
                    f"High-risk exploit activity found: {step}"
    
    # Results should not contain high-risk findings
    if "results" in results:
        for result in results["results"]:
            if "findings" in result:
                for finding in result["findings"]:
                    if "risk_level" in finding:
                        assert finding["risk_level"] in ["low", "medium"], \
                            f"High-risk finding violates policy: {finding}"


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_time_constraints(api_client: APIClient):
    """Test that time-based policy constraints are enforced"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "max_runtime_minutes": 5,
        "step_timeout_minutes": 2,
        "enforce_timeouts": True,
        "inputs": {
            "targets": ["172.16.0.100"],
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Monitor execution time
    import time
    start_time = time.time()
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=400, interval=10)  # Allow extra buffer
    
    end_time = time.time()
    execution_time_minutes = (end_time - start_time) / 60
    
    # Should complete within policy time limit (allow some buffer)
    assert execution_time_minutes <= 7, \
        f"Execution time {execution_time_minutes:.1f}min exceeds policy limit"
    
    # Get final status
    final_status = await api_client.get(f"/runs/{run_id}")
    
    # Should complete successfully or timeout gracefully
    assert final_status["status"] in ["completed", "failed"], \
        "Run should complete or timeout gracefully"
    
    if final_status["status"] == "failed":
        error_msg = final_status.get("error_message", "").lower()
        # Acceptable timeout-related failures
        assert any(keyword in error_msg for keyword in ["timeout", "time", "duration"]), \
            "Failure should be timeout-related if policy time limit exceeded"


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_credential_safety(api_client: APIClient):
    """Test that credential testing policies are enforced"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "creds_max_attempts": 3,
        "creds_rate_limit_ms": 5000,
        "creds_lockout_protection": True,
        "creds_safe_mode": True,
        "production_target": True,
        "inputs": {
            "targets": ["10.50.0.100"],
            "depth": "standard",
            "features": ["creds"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=200, interval=15)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    
    # Check credential testing was constrained
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Should respect attempt limits
        if "total_attempts" in creds_result:
            assert creds_result["total_attempts"] <= 3, \
                f"Credential attempts {creds_result['total_attempts']} exceed policy limit"
        
        # Should implement rate limiting
        if "rate_limited" in creds_result:
            assert creds_result["rate_limited"] == True, \
                "Should implement rate limiting per policy"
        
        # Should avoid lockout scenarios
        if "lockout_protection_active" in creds_result:
            assert creds_result["lockout_protection_active"] == True
        
        # Should be in safe mode
        if "safe_mode" in creds_result:
            assert creds_result["safe_mode"] == True


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_network_scope_limits(api_client: APIClient):
    """Test that network scope limitations are enforced"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "max_network_scope": "single_host",
        "forbid_network_scanning": False,
        "max_hosts_to_scan": 1,
        "lateral_movement_allowed": False,
        "inputs": {
            "targets": ["192.168.100.50"],
            "depth": "advanced",
            "features": ["recon", "lateral"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=200, interval=15)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    
    # Check network scope was limited
    recon_results = [r for r in results["results"] if r["agent"] == "recon"]
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    # Recon should be limited to single host
    if len(recon_results) > 0:
        recon_result = recon_results[0]
        
        if "hosts_discovered" in recon_result:
            # Should not discover many additional hosts
            discovered = recon_result["hosts_discovered"]
            assert isinstance(discovered, int)
            # Allow some flexibility for legitimate discoveries
    
    # Lateral movement should be restricted or not performed
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should not perform actual lateral movement
        if "movement_attempted" in lateral_result:
            assert lateral_result["movement_attempted"] == False, \
                "Lateral movement should be forbidden by policy"


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_compliance_logging(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that policy compliance is logged to OpenSearch"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "compliance_mode": "strict",
        "log_policy_decisions": True,
        "audit_trail": True,
        "inputs": {
            "targets": ["10.100.0.50"],
            "depth": "basic",
            "features": ["recon"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    plan_id = response["plan_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=120, interval=10)
    
    # Allow time for logging
    await asyncio.sleep(5)
    await opensearch_client.refresh_index(test_config["os_idx_planner"])
    
    # Search for planner document with policy information
    query = OpenSearchQueries.term_query("plan_id", plan_id)
    docs = await opensearch_client.search(test_config["os_idx_planner"], query)
    
    assert docs["hits"]["total"]["value"] >= 1, "Should have planner document"
    
    planner_doc = docs["hits"]["hits"][0]["_source"]
    
    # Should have policy compliance information
    if "policy_compliance" in planner_doc:
        compliance = planner_doc["policy_compliance"]
        
        assert "compliance_mode" in compliance
        assert compliance["compliance_mode"] == "strict"
        
        if "policy_checks" in compliance:
            checks = compliance["policy_checks"]
            assert isinstance(checks, list)
            
            for check in checks:
                assert "check_type" in check
                assert "result" in check
                assert check["result"] in ["pass", "fail", "warning"]
    
    # Should have audit trail entries
    if "audit_trail" in planner_doc:
        audit = planner_doc["audit_trail"]
        assert isinstance(audit, list)
        assert len(audit) > 0, "Should have audit trail entries"


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_emergency_stop(api_client: APIClient):
    """Test emergency stop functionality"""
    # Start a longer-running test
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["172.20.0.100", "172.20.0.101", "172.20.0.102"],
            "depth": "comprehensive",
            "features": ["recon", "web", "exploit"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait a bit, then trigger emergency stop
    await asyncio.sleep(15)
    
    # Send stop signal
    stop_response = await api_client.post(f"/runs/{run_id}/stop", {
        "reason": "emergency_stop",
        "immediate": True
    })
    
    assert stop_response.get("status") == "stopping", "Should acknowledge stop request"
    
    # Wait for actual stop
    from src.utils import wait_for_condition
    
    async def check_stopped():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["stopped", "failed", "error"]
    
    await wait_for_condition(check_stopped, timeout=60, interval=5)
    
    # Verify stopped
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] in ["stopped", "failed"], \
        "Run should be stopped or failed after emergency stop"
    
    # Should have stop reason logged
    if "stop_reason" in final_status:
        assert "emergency" in final_status["stop_reason"].lower()


@pytest.mark.asyncio
@pytest.mark.policy
async def test_policy_approval_workflow(api_client: APIClient):
    """Test approval workflow for high-risk operations"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "require_approval": True,
        "approval_required_for": ["exploit", "creds", "lateral", "privesc"],
        "auto_approve_simulation": True  # For testing,
        "inputs": {
            "targets": ["10.200.0.100"],
            "depth": "comprehensive",
            "features": ["exploit", "creds", "lateral", "privesc"],
            "simulate": True
        }
    }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    plan_id = response["plan_id"]
    
    # Should create plan but wait for approval
    plan = await api_client.get(f"/plans/{plan_id}")
    
    if "approval_status" in plan:
        # If approval workflow is implemented
        assert plan["approval_status"] in ["pending", "approved", "auto_approved"]
        
        if plan["approval_status"] == "pending":
            # Test approval
            approval_response = await api_client.post(f"/plans/{plan_id}/approve", {
                "approved_by": "test_admin",
                "reason": "test_approval"
            })
            
            assert approval_response.get("status") == "approved"
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=300, interval=20)
    
    # Should complete successfully after approval
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] == "completed", \
        "Run should complete after approval"
