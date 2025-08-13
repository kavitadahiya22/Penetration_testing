"""
End-to-end tests for planner functionality
Tests dynamic planning with various inputs and validates OpenSearch logging
"""
import pytest
import asyncio
import json
from typing import Dict, Any

from src.utils import APIClient, validate_response_schema, load_test_data
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id, generate_timestamp


@pytest.mark.asyncio
@pytest.mark.planner
@pytest.mark.smoke
async def test_planner_basic_recon(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test basic reconnaissance planning"""
    # Prepare test input
    plan_input = {
        "targets": ["127.0.0.1/32"],
        "depth": "basic",
        "features": ["recon"],
        "simulate": True,
        "tenant_id": generate_test_tenant_id()
    }
    
    # Create plan
    response = await api_client.post("/planner/plan", plan_input)
    
    # Validate response structure
    validate_response_schema(response, [
        "plan_id", "tenant_id", "created_at", "targets", "depth", 
        "features", "steps", "estimated_duration"
    ])
    
    plan_id = response["plan_id"]
    
    # Validate plan content
    assert response["depth"] == "basic"
    assert "recon" in response["features"]
    assert len(response["steps"]) >= 1
    assert all(step["agent"] == "recon" for step in response["steps"])
    
    # Wait for planner record in OpenSearch
    await asyncio.sleep(2)
    await opensearch_client.refresh_index(test_config["os_idx_planner"])
    
    query = OpenSearchQueries.term_query("plan_id", plan_id)
    planner_docs = await opensearch_client.search(test_config["os_idx_planner"], query)
    
    assert planner_docs["hits"]["total"]["value"] >= 1
    planner_doc = planner_docs["hits"]["hits"][0]["_source"]
    
    # Validate planner document
    assert planner_doc["plan_id"] == plan_id
    assert planner_doc["tenant_id"] == plan_input["tenant_id"]
    assert planner_doc["depth"] == "basic"
    assert "recon" in planner_doc["features"]
    assert planner_doc["steps_count"] >= 1


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_web_vulnerability_scan(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test web vulnerability scanning plan"""
    plan_input = {
        "targets": ["http://test-target/", "https://httpbin.org/get"],
        "depth": "standard",
        "features": ["web", "vuln"],
        "simulate": True,
        "tenant_id": generate_test_tenant_id()
    }
    
    response = await api_client.post("/planner/plan", plan_input)
    
    # Validate response
    validate_response_schema(response, [
        "plan_id", "steps", "features", "targets"
    ])
    
    # Check that web agent is included
    agents_used = set(step["agent"] for step in response["steps"])
    assert "web" in agents_used
    
    # Check that appropriate tools are planned
    tools_used = set(step["tool"] for step in response["steps"])
    expected_tools = {"zap", "nikto"}
    assert len(expected_tools.intersection(tools_used)) > 0
    
    # Verify OpenSearch logging
    await asyncio.sleep(2)
    await opensearch_client.refresh_index(test_config["os_idx_planner"])
    
    query = OpenSearchQueries.term_query("plan_id", response["plan_id"])
    planner_docs = await opensearch_client.search(test_config["os_idx_planner"], query)
    
    assert planner_docs["hits"]["total"]["value"] >= 1


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_comprehensive_pentest(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test comprehensive penetration test planning"""
    plan_input = {
        "targets": ["10.0.1.0/24", "test.example.com", "http://app.test/"],
        "depth": "comprehensive",
        "features": ["recon", "web", "vuln", "creds", "lateral", "priv-esc"],
        "simulate": True,
        "tenant_id": generate_test_tenant_id()
    }
    
    response = await api_client.post("/planner/plan", plan_input)
    
    # Validate comprehensive plan
    validate_response_schema(response, [
        "plan_id", "steps", "features", "targets", "methodology"
    ])
    
    # Should have multiple agents
    agents_used = set(step["agent"] for step in response["steps"])
    expected_agents = {"recon", "web", "creds"}  # Minimum expected
    assert len(expected_agents.intersection(agents_used)) >= 2
    
    # Should have reasonable number of steps for comprehensive test
    assert len(response["steps"]) >= 5
    assert len(response["steps"]) <= 30  # Reasonable upper bound
    
    # Check dependencies are properly set
    step_ids = [step["step_id"] for step in response["steps"]]
    for step in response["steps"]:
        if step.get("dependencies"):
            for dep in step["dependencies"]:
                assert dep in step_ids, f"Invalid dependency {dep} in step {step['step_id']}"


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_with_policy_constraints(api_client: APIClient, test_config: Dict):
    """Test planner respects policy constraints"""
    # Test with targets outside allowed networks
    plan_input = {
        "targets": ["8.8.8.8"],  # Public DNS - should be blocked
        "depth": "basic",
        "features": ["recon"],
        "simulate": True,
        "tenant_id": generate_test_tenant_id()
    }
    
    # This should either be rejected or modified by policy
    try:
        response = await api_client.post("/planner/plan", plan_input)
        
        # If accepted, check that targets were modified or plan was restricted
        if "plan_id" in response:
            # Plan should be modified to comply with policy
            assert len(response.get("steps", [])) == 0 or \
                   all(step.get("risk_level", "low") in ["low", "medium"] for step in response["steps"])
    except Exception as e:
        # Rejection is also acceptable behavior
        assert "not allowed" in str(e).lower() or "policy" in str(e).lower()


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_exploit_simulation_mode(api_client: APIClient, test_config: Dict):
    """Test that exploit features require simulation mode"""
    plan_input = {
        "targets": ["10.0.1.1"],
        "depth": "advanced",
        "features": ["exploit"],
        "simulate": False,  # Should be blocked or forced to simulation
        "tenant_id": generate_test_tenant_id()
    }
    
    response = await api_client.post("/planner/plan", plan_input)
    
    # Either plan should be rejected, or all exploit steps should be simulation-only
    if "plan_id" in response:
        exploit_steps = [step for step in response["steps"] if step["agent"] == "exploit"]
        for step in exploit_steps:
            # Should have simulation flag or be marked as preview-only
            assert step.get("simulate", True) or step.get("preview_only", True) or \
                   step.get("risk_level") == "blocked"


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_step_dependencies(api_client: APIClient, test_config: Dict):
    """Test that planner creates proper step dependencies"""
    plan_input = {
        "targets": ["10.0.1.0/24"],
        "depth": "standard",
        "features": ["recon", "creds"],
        "simulate": True,
        "tenant_id": generate_test_tenant_id()
    }
    
    response = await api_client.post("/planner/plan", plan_input)
    
    steps = response["steps"]
    
    # Find recon and creds steps
    recon_steps = [step for step in steps if step["agent"] == "recon"]
    creds_steps = [step for step in steps if step["agent"] == "creds"]
    
    if recon_steps and creds_steps:
        # Creds steps should depend on recon steps
        recon_step_ids = [step["step_id"] for step in recon_steps]
        
        for creds_step in creds_steps:
            dependencies = creds_step.get("dependencies", [])
            # Should have at least one dependency on recon
            assert any(dep in recon_step_ids for dep in dependencies), \
                f"Creds step {creds_step['step_id']} should depend on recon step"


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_target_type_validation(api_client: APIClient, test_config: Dict):
    """Test planner handles different target types correctly"""
    scenarios = [
        {
            "name": "IP address",
            "targets": ["192.168.1.1"],
            "expected_agents": ["recon"]
        },
        {
            "name": "IP range",
            "targets": ["192.168.1.0/24"],
            "expected_agents": ["recon"]
        },
        {
            "name": "Domain",
            "targets": ["test.example.com"],
            "expected_agents": ["recon"]
        },
        {
            "name": "URL",
            "targets": ["http://test.example.com/"],
            "expected_agents": ["web"]
        },
        {
            "name": "Mixed targets",
            "targets": ["192.168.1.1", "http://test.example.com/"],
            "expected_agents": ["recon", "web"]
        }
    ]
    
    for scenario in scenarios:
        plan_input = {
            "targets": scenario["targets"],
            "depth": "basic",
            "features": ["recon", "web"],
            "simulate": True,
            "tenant_id": generate_test_tenant_id()
        }
        
        response = await api_client.post("/planner/plan", plan_input)
        
        agents_used = set(step["agent"] for step in response["steps"])
        
        # Check that appropriate agents are used for target types
        for expected_agent in scenario["expected_agents"]:
            assert expected_agent in agents_used, \
                f"Expected agent {expected_agent} for scenario {scenario['name']}"


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_depth_scaling(api_client: APIClient, test_config: Dict):
    """Test that plan complexity scales with depth parameter"""
    target = ["192.168.1.1"]
    tenant_id = generate_test_tenant_id()
    
    depths = ["basic", "standard", "advanced", "comprehensive"]
    step_counts = []
    
    for depth in depths:
        plan_input = {
            "targets": target,
            "depth": depth,
            "features": ["recon", "web"],
            "simulate": True,
            "tenant_id": tenant_id
        }
        
        response = await api_client.post("/planner/plan", plan_input)
        step_counts.append(len(response["steps"]))
    
    # Generally, deeper scans should have more steps
    # Allow some flexibility but ensure general trend
    assert step_counts[0] <= step_counts[1], "Standard should have >= steps than basic"
    assert step_counts[-1] >= step_counts[0], "Comprehensive should have >= steps than basic"


@pytest.mark.asyncio
@pytest.mark.planner
async def test_planner_opensearch_schema_validation(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that planner documents in OpenSearch have correct schema"""
    # Search for recent planner documents
    query = OpenSearchQueries.range_query(
        "created_at",
        gte="now-1h"
    )
    
    await opensearch_client.refresh_index(test_config["os_idx_planner"])
    docs = await opensearch_client.search(test_config["os_idx_planner"], query, size=5)
    
    if docs["hits"]["total"]["value"] > 0:
        doc = docs["hits"]["hits"][0]["_source"]
        
        # Required fields
        required_fields = [
            "plan_id", "tenant_id", "created_at", "model_provider",
            "targets", "depth", "features", "steps_count"
        ]
        
        for field in required_fields:
            assert field in doc, f"Missing required field: {field}"
        
        # Validate field types
        assert isinstance(doc["steps_count"], int)
        assert isinstance(doc["features"], list)
        assert doc["depth"] in ["basic", "standard", "advanced", "comprehensive"]
        
        # Validate plan_id format
        assert doc["plan_id"].startswith("plan-"), "plan_id should start with 'plan-'"
        
        # Validate timestamp format
        from src.utils import is_valid_iso_datetime
        assert is_valid_iso_datetime(doc["created_at"]), "created_at should be valid ISO datetime"
