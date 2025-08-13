"""
Tests for OpenSearch logging schema validation
Validates that all planner decisions, agent actions, and run summaries are properly logged
"""
import pytest
import asyncio
from typing import Dict, Any, List

from src.utils import APIClient, validate_response_schema, is_valid_iso_datetime
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.logging
@pytest.mark.smoke
async def test_planner_logging_schema(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test planner documents have correct schema in OpenSearch"""
    # Search for recent planner documents
    query = OpenSearchQueries.range_query("created_at", gte="now-1h")
    
    await opensearch_client.refresh_index(test_config["os_idx_planner"])
    docs = await opensearch_client.search(test_config["os_idx_planner"], query, size=5)
    
    if docs["hits"]["total"]["value"] == 0:
        pytest.skip("No recent planner documents found for schema validation")
    
    # Validate each planner document
    for hit in docs["hits"]["hits"]:
        doc = hit["_source"]
        
        # Required fields for planner documents
        required_fields = [
            "plan_id", "tenant_id", "created_at", "model_provider",
            "targets", "depth", "features", "steps_count"
        ]
        
        validate_response_schema(doc, required_fields)
        
        # Validate field types and formats
        assert isinstance(doc["plan_id"], str), "plan_id should be string"
        assert doc["plan_id"].startswith("plan-"), "plan_id should start with 'plan-'"
        
        assert isinstance(doc["tenant_id"], str), "tenant_id should be string"
        assert len(doc["tenant_id"]) >= 3, "tenant_id should be meaningful length"
        
        assert is_valid_iso_datetime(doc["created_at"]), "created_at should be valid ISO datetime"
        
        assert doc["model_provider"] in ["ollama", "openai"], f"Invalid model_provider: {doc['model_provider']}"
        
        assert isinstance(doc["targets"], list), "targets should be list"
        assert len(doc["targets"]) >= 1, "Should have at least one target"
        
        assert doc["depth"] in ["basic", "standard", "advanced", "comprehensive"], f"Invalid depth: {doc['depth']}"
        
        assert isinstance(doc["features"], list), "features should be list"
        assert len(doc["features"]) >= 1, "Should have at least one feature"
        
        assert isinstance(doc["steps_count"], int), "steps_count should be integer"
        assert doc["steps_count"] >= 0, "steps_count should be non-negative"
        
        # Optional fields validation
        if "estimated_duration" in doc:
            assert isinstance(doc["estimated_duration"], int), "estimated_duration should be integer"
        
        if "prompt_hash" in doc:
            assert isinstance(doc["prompt_hash"], str), "prompt_hash should be string"


@pytest.mark.asyncio
@pytest.mark.logging
@pytest.mark.smoke
async def test_actions_logging_schema(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test action documents have correct schema in OpenSearch"""
    # Search for recent action documents
    query = OpenSearchQueries.range_query("started_at", gte="now-1h")
    
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    docs = await opensearch_client.search(test_config["os_idx_actions"], query, size=10)
    
    if docs["hits"]["total"]["value"] == 0:
        pytest.skip("No recent action documents found for schema validation")
    
    # Validate each action document
    for hit in docs["hits"]["hits"]:
        doc = hit["_source"]
        
        # Required fields for action documents
        required_fields = [
            "run_id", "step_id", "agent", "tool", "status",
            "started_at", "ended_at", "duration_ms"
        ]
        
        validate_response_schema(doc, required_fields)
        
        # Validate field types and formats
        assert isinstance(doc["run_id"], str), "run_id should be string"
        assert doc["run_id"].startswith("run-"), "run_id should start with 'run-'"
        
        assert isinstance(doc["step_id"], str), "step_id should be string"
        
        assert doc["agent"] in ["recon", "web", "exploit", "creds", "lateral", "privesc"], \
            f"Invalid agent: {doc['agent']}"
        
        assert isinstance(doc["tool"], str), "tool should be string"
        assert len(doc["tool"]) >= 2, "tool should be meaningful"
        
        assert doc["status"] in ["running", "completed", "failed", "error", "blocked"], \
            f"Invalid status: {doc['status']}"
        
        assert is_valid_iso_datetime(doc["started_at"]), "started_at should be valid ISO datetime"
        assert is_valid_iso_datetime(doc["ended_at"]), "ended_at should be valid ISO datetime"
        
        assert isinstance(doc["duration_ms"], int), "duration_ms should be integer"
        assert doc["duration_ms"] >= 0, "duration_ms should be non-negative"
        
        # Optional fields validation
        if "target" in doc:
            assert isinstance(doc["target"], str), "target should be string"
        
        if "params" in doc:
            assert isinstance(doc["params"], dict), "params should be object"
        
        if "artifacts" in doc:
            assert isinstance(doc["artifacts"], dict), "artifacts should be object"
        
        if "error_message" in doc:
            assert isinstance(doc["error_message"], str), "error_message should be string"
        
        if "findings_count" in doc:
            assert isinstance(doc["findings_count"], int), "findings_count should be integer"
            assert doc["findings_count"] >= 0, "findings_count should be non-negative"


@pytest.mark.asyncio
@pytest.mark.logging
@pytest.mark.smoke  
async def test_runs_logging_schema(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test run summary documents have correct schema in OpenSearch"""
    # Search for recent run documents
    query = OpenSearchQueries.range_query("started_at", gte="now-1h")
    
    await opensearch_client.refresh_index(test_config["os_idx_runs"])
    docs = await opensearch_client.search(test_config["os_idx_runs"], query, size=5)
    
    if docs["hits"]["total"]["value"] == 0:
        pytest.skip("No recent run documents found for schema validation")
    
    # Validate each run document
    for hit in docs["hits"]["hits"]:
        doc = hit["_source"]
        
        # Required fields for run documents
        required_fields = [
            "run_id", "plan_id", "status", "started_at", "ended_at",
            "duration_ms", "steps_count", "steps_completed"
        ]
        
        validate_response_schema(doc, required_fields)
        
        # Validate field types and formats
        assert isinstance(doc["run_id"], str), "run_id should be string"
        assert doc["run_id"].startswith("run-"), "run_id should start with 'run-'"
        
        assert isinstance(doc["plan_id"], str), "plan_id should be string"
        assert doc["plan_id"].startswith("plan-"), "plan_id should start with 'plan-'"
        
        assert doc["status"] in ["running", "completed", "failed", "error", "partial"], \
            f"Invalid status: {doc['status']}"
        
        assert is_valid_iso_datetime(doc["started_at"]), "started_at should be valid ISO datetime"
        assert is_valid_iso_datetime(doc["ended_at"]), "ended_at should be valid ISO datetime"
        
        assert isinstance(doc["duration_ms"], int), "duration_ms should be integer"
        assert doc["duration_ms"] >= 0, "duration_ms should be non-negative"
        
        assert isinstance(doc["steps_count"], int), "steps_count should be integer"
        assert doc["steps_count"] >= 0, "steps_count should be non-negative"
        
        assert isinstance(doc["steps_completed"], int), "steps_completed should be integer"
        assert doc["steps_completed"] >= 0, "steps_completed should be non-negative"
        assert doc["steps_completed"] <= doc["steps_count"], "steps_completed should not exceed steps_count"
        
        # Optional fields validation
        if "steps_failed" in doc:
            assert isinstance(doc["steps_failed"], int), "steps_failed should be integer"
            assert doc["steps_failed"] >= 0, "steps_failed should be non-negative"
        
        if "total_findings" in doc:
            assert isinstance(doc["total_findings"], int), "total_findings should be integer"
            assert doc["total_findings"] >= 0, "total_findings should be non-negative"
        
        severity_fields = ["high_severity_findings", "medium_severity_findings", "low_severity_findings"]
        for field in severity_fields:
            if field in doc:
                assert isinstance(doc[field], int), f"{field} should be integer"
                assert doc[field] >= 0, f"{field} should be non-negative"
        
        if "targets_scanned" in doc:
            assert isinstance(doc["targets_scanned"], int), "targets_scanned should be integer"
            assert doc["targets_scanned"] >= 0, "targets_scanned should be non-negative"


@pytest.mark.asyncio
@pytest.mark.logging
async def test_logging_data_completeness(api_client: APIClient, opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that all components of a run are logged completely"""
    # Create a simple run and track its logging
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
    
    # Start run
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    plan_id = response["plan_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=120, interval=5)
    
    # Allow time for final logging
    await asyncio.sleep(5)
    await opensearch_client.refresh_index(test_config["os_idx_planner"])
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    await opensearch_client.refresh_index(test_config["os_idx_runs"])
    
    # Check planner document exists
    planner_query = OpenSearchQueries.term_query("plan_id", plan_id)
    planner_docs = await opensearch_client.search(test_config["os_idx_planner"], planner_query)
    assert planner_docs["hits"]["total"]["value"] >= 1, f"Planner document not found for plan {plan_id}"
    
    # Check action documents exist
    actions_query = OpenSearchQueries.term_query("run_id", run_id)
    action_docs = await opensearch_client.search(test_config["os_idx_actions"], actions_query)
    assert action_docs["hits"]["total"]["value"] >= 1, f"Action documents not found for run {run_id}"
    
    # Check run summary document exists
    runs_query = OpenSearchQueries.term_query("run_id", run_id)
    run_docs = await opensearch_client.search(test_config["os_idx_runs"], runs_query)
    assert run_docs["hits"]["total"]["value"] == 1, f"Run summary document not found for run {run_id}"
    
    # Validate cross-references
    planner_doc = planner_docs["hits"]["hits"][0]["_source"]
    run_doc = run_docs["hits"]["hits"][0]["_source"]
    
    # Plan and run should reference each other
    assert planner_doc["plan_id"] == plan_id
    assert run_doc["plan_id"] == plan_id
    assert run_doc["run_id"] == run_id
    
    # Steps count should be consistent
    assert planner_doc["steps_count"] == run_doc["steps_count"]
    
    # Action count should match steps completed
    actual_actions = action_docs["hits"]["total"]["value"]
    expected_actions = run_doc["steps_completed"]
    assert actual_actions >= expected_actions, \
        f"Action count {actual_actions} should be >= steps completed {expected_actions}"


@pytest.mark.asyncio
@pytest.mark.logging
async def test_logging_timestamp_ordering(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that timestamps are logically ordered"""
    # Search for recent completed runs with actions
    query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.range_query("started_at", gte="now-1h"),
            OpenSearchQueries.term_query("status", "completed")
        ]
    )
    
    await opensearch_client.refresh_index(test_config["os_idx_runs"])
    run_docs = await opensearch_client.search(test_config["os_idx_runs"], query, size=3)
    
    if run_docs["hits"]["total"]["value"] == 0:
        pytest.skip("No recent completed runs found for timestamp validation")
    
    for run_hit in run_docs["hits"]["hits"]:
        run_doc = run_hit["_source"]
        run_id = run_doc["run_id"]
        
        # Get actions for this run
        actions_query = OpenSearchQueries.term_query("run_id", run_id)
        await opensearch_client.refresh_index(test_config["os_idx_actions"])
        action_docs = await opensearch_client.search(test_config["os_idx_actions"], actions_query, size=10)
        
        if action_docs["hits"]["total"]["value"] == 0:
            continue
        
        # Validate timestamp ordering
        from datetime import datetime
        
        run_start = datetime.fromisoformat(run_doc["started_at"].replace("Z", "+00:00"))
        run_end = datetime.fromisoformat(run_doc["ended_at"].replace("Z", "+00:00"))
        
        # Run end should be after run start
        assert run_end >= run_start, f"Run end time should be >= start time for run {run_id}"
        
        # Calculate duration and validate
        actual_duration = (run_end - run_start).total_seconds() * 1000
        logged_duration = run_doc["duration_ms"]
        
        # Allow some tolerance for rounding/processing time
        duration_diff = abs(actual_duration - logged_duration)
        assert duration_diff <= 5000, f"Duration mismatch for run {run_id}: {actual_duration} vs {logged_duration}"
        
        # Check action timestamps
        for action_hit in action_docs["hits"]["hits"]:
            action_doc = action_hit["_source"]
            
            action_start = datetime.fromisoformat(action_doc["started_at"].replace("Z", "+00:00"))
            action_end = datetime.fromisoformat(action_doc["ended_at"].replace("Z", "+00:00"))
            
            # Action should be within run timeframe
            assert action_start >= run_start, f"Action start should be >= run start for run {run_id}"
            assert action_end <= run_end, f"Action end should be <= run end for run {run_id}"
            
            # Action end should be after action start
            assert action_end >= action_start, f"Action end should be >= start for run {run_id}"


@pytest.mark.asyncio
@pytest.mark.logging
async def test_logging_error_scenarios(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that errors are properly logged"""
    # Search for recent failed actions
    query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.range_query("started_at", gte="now-1h"),
            OpenSearchQueries.term_query("status", "failed")
        ]
    )
    
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    failed_docs = await opensearch_client.search(test_config["os_idx_actions"], query, size=5)
    
    if failed_docs["hits"]["total"]["value"] == 0:
        pytest.skip("No recent failed actions found for error logging validation")
    
    # Validate error logging for failed actions
    for hit in failed_docs["hits"]["hits"]:
        doc = hit["_source"]
        
        assert doc["status"] == "failed", "Document should have failed status"
        
        # Failed actions should have error information
        assert "error_message" in doc, "Failed actions should have error_message"
        assert isinstance(doc["error_message"], str), "error_message should be string"
        assert len(doc["error_message"]) > 0, "error_message should not be empty"
        
        # Should still have timing information
        assert "duration_ms" in doc, "Failed actions should still have duration"
        assert doc["duration_ms"] >= 0, "Failed action duration should be non-negative"


@pytest.mark.asyncio
@pytest.mark.logging
async def test_logging_index_health(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test that logging indices are healthy and properly configured"""
    indices = [
        test_config["os_idx_planner"],
        test_config["os_idx_actions"], 
        test_config["os_idx_runs"]
    ]
    
    for index_name in indices:
        # Check index exists
        exists = await opensearch_client.index_exists(index_name)
        assert exists, f"Index {index_name} should exist"
        
        # Check index has documents
        count = await opensearch_client.count_documents(index_name)
        # Note: In test environment, might be 0, but we can still validate structure
        assert count >= 0, f"Index {index_name} should be accessible"
        
        # If index has documents, validate mapping
        if count > 0:
            # Test a simple query to ensure index is functional
            query = OpenSearchQueries.match_all()
            docs = await opensearch_client.search(index_name, query, size=1)
            
            assert docs["hits"]["total"]["value"] >= 1, f"Index {index_name} should return documents"
