"""
Tests for the Privilege Escalation Agent
Validates BloodHound integration, privilege path discovery, escalation techniques, and safety controls
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.utils import APIClient, validate_response_schema, DataManager
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.privesc
@pytest.mark.smoke
async def test_privesc_agent_basic_enumeration(api_client: APIClient):
    """Test privilege escalation agent performs basic privilege enumeration"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "enumeration_only",
        "identify_paths": True,
        "max_risk_level": "medium",
        "inputs": {
            "targets": ["10.0.0.200"],
            "depth": "basic",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=200, interval=15)
    
    # Get final status
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] == "completed"
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    
    # Should have privilege escalation results
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    assert len(privesc_results) > 0, "Should have privilege escalation agent results"
    
    # Validate privesc result structure
    privesc_result = privesc_results[0]
    required_fields = ["agent", "target", "privilege_paths", "current_privileges"]
    validate_response_schema(privesc_result, required_fields)
    
    assert privesc_result["agent"] == "privesc"
    assert isinstance(privesc_result["privilege_paths"], list)
    assert isinstance(privesc_result["current_privileges"], dict)


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_bloodhound_integration(api_client: APIClient):
    """Test privilege escalation agent integrates with BloodHound for path analysis"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "bloodhound_analysis",
        "use_bloodhound": True,
        "target_privileges": ["domain_admin", "enterprise_admin"],
        "max_path_length": 5,
        "inputs": {
            "targets": ["172.16.2.100"],
            "depth": "advanced",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=300, interval=20)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    assert len(privesc_results) > 0, "Should have privilege escalation results"
    
    # Validate BloodHound integration
    privesc_result = privesc_results[0]
    
    if "tools_used" in privesc_result:
        tools = [tool.lower() for tool in privesc_result["tools_used"]]
        assert any("bloodhound" in tool for tool in tools), "Should use BloodHound"
    
    # Should have privilege escalation paths
    if "escalation_paths" in privesc_result:
        paths = privesc_result["escalation_paths"]
        assert isinstance(paths, list)
        
        for path in paths:
            required_path_fields = ["source", "target", "steps", "complexity"]
            validate_response_schema(path, required_path_fields)
            
            assert path["complexity"] in ["low", "medium", "high", "very_high"]
            assert isinstance(path["steps"], list)
            assert len(path["steps"]) <= 5, "Should respect max_path_length"
            
            # Validate step structure
            for step in path["steps"]:
                assert "relationship" in step
                assert "source" in step
                assert "target" in step
                
                # Common BloodHound relationships for privilege escalation
                valid_relationships = [
                    "AdminTo", "MemberOf", "HasSession", "CanRDP", "ExecuteDCOM",
                    "AllowedToDelegate", "ForceChangePassword", "GenericAll",
                    "WriteDacl", "WriteOwner", "Owns"
                ]
                assert step["relationship"] in valid_relationships
    
    # Should identify target privileges
    if "target_analysis" in privesc_result:
        target_analysis = privesc_result["target_analysis"]
        
        target_privs = ["domain_admin", "enterprise_admin"]
        for target_priv in target_privs:
            if target_priv in target_analysis:
                priv_info = target_analysis[target_priv]
                assert "reachable" in priv_info
                assert isinstance(priv_info["reachable"], bool)
                
                if priv_info["reachable"]:
                    assert "shortest_path_length" in priv_info
                    assert isinstance(priv_info["shortest_path_length"], int)


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_windows_techniques(api_client: APIClient):
    """Test privilege escalation agent identifies Windows-specific escalation techniques"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "windows_techniques",
        "check_services": True,
        "check_registry": True,
        "check_tokens": True,
        "check_files": True,
        "inputs": {
            "targets": ["10.10.2.150"],
            "depth": "comprehensive",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=350, interval=25)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    if len(privesc_results) > 0:
        privesc_result = privesc_results[0]
        
        # Should identify Windows privilege escalation techniques
        if "techniques_identified" in privesc_result:
            techniques = privesc_result["techniques_identified"]
            assert isinstance(techniques, list)
            
            # Common Windows privilege escalation techniques
            windows_techniques = [
                "unquoted_service_path", "service_permissions", "registry_autoruns",
                "dll_hijacking", "token_impersonation", "always_install_elevated",
                "weak_file_permissions", "scheduled_tasks", "vulnerable_drivers"
            ]
            
            for technique in techniques:
                assert "technique_name" in technique
                assert "severity" in technique
                assert technique["severity"] in ["critical", "high", "medium", "low"]
                
                if "details" in technique:
                    details = technique["details"]
                    
                    # Technique-specific validation
                    if technique["technique_name"] == "unquoted_service_path":
                        assert "service_name" in details
                        assert "path" in details
                    
                    elif technique["technique_name"] == "service_permissions":
                        assert "service_name" in details
                        assert "permissions" in details
                    
                    elif technique["technique_name"] == "registry_autoruns":
                        assert "registry_key" in details
                        assert "value" in details
        
        # Should check service vulnerabilities
        if "service_analysis" in privesc_result:
            service_analysis = privesc_result["service_analysis"]
            
            if "vulnerable_services" in service_analysis:
                vuln_services = service_analysis["vulnerable_services"]
                assert isinstance(vuln_services, list)
                
                for service in vuln_services:
                    assert "service_name" in service
                    assert "vulnerability_type" in service
                    assert "exploitable" in service
                    assert isinstance(service["exploitable"], bool)
        
        # Should analyze token privileges
        if "token_analysis" in privesc_result:
            token_analysis = privesc_result["token_analysis"]
            
            if "current_privileges" in token_analysis:
                current_privs = token_analysis["current_privileges"]
                assert isinstance(current_privs, list)
                
                # Common Windows privileges
                privilege_names = [
                    "SeDebugPrivilege", "SeImpersonatePrivilege", "SeAssignPrimaryTokenPrivilege",
                    "SeTcbPrivilege", "SeBackupPrivilege", "SeRestorePrivilege"
                ]
                
                for priv in current_privs:
                    if "name" in priv:
                        # Should be recognizable Windows privilege
                        assert any(known_priv in priv["name"] for known_priv in privilege_names) or \
                               priv["name"].startswith("Se"), \
                               f"Unrecognized privilege format: {priv['name']}"
                    
                    if "enabled" in priv:
                        assert isinstance(priv["enabled"], bool)


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_linux_techniques(api_client: APIClient):
    """Test privilege escalation agent identifies Linux-specific escalation techniques"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "linux_techniques",
        "check_sudo": True,
        "check_suid": True,
        "check_capabilities": True,
        "check_cron": True,
        "target_os": "linux",
        "inputs": {
            "targets": ["192.168.30.100"],
            "depth": "advanced",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=280, interval=20)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    if len(privesc_results) > 0:
        privesc_result = privesc_results[0]
        
        # Should identify Linux privilege escalation techniques
        if "linux_techniques" in privesc_result:
            linux_techniques = privesc_result["linux_techniques"]
            
            # Check SUDO analysis
            if "sudo_analysis" in linux_techniques:
                sudo_analysis = linux_techniques["sudo_analysis"]
                
                if "sudo_entries" in sudo_analysis:
                    sudo_entries = sudo_analysis["sudo_entries"]
                    assert isinstance(sudo_entries, list)
                    
                    for entry in sudo_entries:
                        if "command" in entry:
                            assert isinstance(entry["command"], str)
                        if "escalation_potential" in entry:
                            assert entry["escalation_potential"] in ["high", "medium", "low"]
            
            # Check SUID binaries
            if "suid_analysis" in linux_techniques:
                suid_analysis = linux_techniques["suid_analysis"]
                
                if "suid_binaries" in suid_analysis:
                    suid_binaries = suid_analysis["suid_binaries"]
                    assert isinstance(suid_binaries, list)
                    
                    for binary in suid_binaries:
                        assert "path" in binary
                        assert "owner" in binary
                        
                        if "gtfobins_match" in binary:
                            assert isinstance(binary["gtfobins_match"], bool)
            
            # Check capabilities
            if "capabilities_analysis" in linux_techniques:
                cap_analysis = linux_techniques["capabilities_analysis"]
                
                if "interesting_capabilities" in cap_analysis:
                    capabilities = cap_analysis["interesting_capabilities"]
                    assert isinstance(capabilities, list)
                    
                    for cap in capabilities:
                        assert "binary" in cap
                        assert "capabilities" in cap
                        
                        # Common dangerous capabilities
                        dangerous_caps = ["cap_setuid", "cap_setgid", "cap_dac_override"]
                        if any(dangerous in cap["capabilities"].lower() for dangerous in dangerous_caps):
                            assert "risk_level" in cap
            
            # Check cron jobs
            if "cron_analysis" in linux_techniques:
                cron_analysis = linux_techniques["cron_analysis"]
                
                if "writable_cron_files" in cron_analysis:
                    writable_crons = cron_analysis["writable_cron_files"]
                    assert isinstance(writable_crons, list)
                    
                    for cron in writable_crons:
                        assert "path" in cron
                        assert "permissions" in cron


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_safety_constraints(api_client: APIClient):
    """Test privilege escalation agent respects safety constraints"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "safe_enumeration",
        "no_exploitation": True,
        "read_only_checks": True,
        "avoid_system_changes": True,
        "production_target": True,
        "max_risk_level": "low",
        "inputs": {
            "targets": ["10.50.2.100"],
            "depth": "basic",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=180, interval=15)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    if len(privesc_results) > 0:
        privesc_result = privesc_results[0]
        
        # Should not perform exploitation
        assert privesc_result.get("exploitation_attempted", False) == False, \
            "Should not attempt privilege escalation exploitation"
        
        # Should use only safe enumeration techniques
        if "techniques_used" in privesc_result:
            techniques = privesc_result["techniques_used"]
            
            # Should not contain dangerous techniques
            dangerous_techniques = ["exploit", "write", "modify", "execute", "hijack"]
            for technique in techniques:
                assert not any(danger in technique.lower() for danger in dangerous_techniques), \
                    f"Found dangerous technique: {technique}"
        
        # Should respect risk level limits
        if "findings" in privesc_result:
            for finding in privesc_result["findings"]:
                if "risk_level" in finding:
                    assert finding["risk_level"] in ["low", "info"], \
                        f"Finding risk level {finding['risk_level']} exceeds maximum"
        
        # Should be production-safe
        if "production_safe" in privesc_result:
            assert privesc_result["production_safe"] == True
        
        # Should avoid system changes
        if "system_changes_made" in privesc_result:
            assert privesc_result["system_changes_made"] == False


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_attack_path_scoring(api_client: APIClient):
    """Test privilege escalation agent scores attack paths by difficulty and impact"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "path_scoring",
        "score_attack_paths": True,
        "prioritize_by_impact": True,
        "include_difficulty": True,
        "inputs": {
            "targets": ["172.25.0.200"],
            "depth": "advanced",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=300, interval=20)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    if len(privesc_results) > 0:
        privesc_result = privesc_results[0]
        
        # Should have scored attack paths
        if "scored_paths" in privesc_result:
            scored_paths = privesc_result["scored_paths"]
            assert isinstance(scored_paths, list)
            
            for path in scored_paths:
                # Should have scoring information
                assert "difficulty_score" in path
                assert "impact_score" in path
                assert "overall_score" in path
                
                # Validate scoring ranges (typically 0-10)
                assert 0 <= path["difficulty_score"] <= 10
                assert 0 <= path["impact_score"] <= 10
                assert 0 <= path["overall_score"] <= 10
                
                # Should have path details
                assert "technique" in path
                assert "target_privilege" in path
                
                if "prerequisites" in path:
                    prereqs = path["prerequisites"]
                    assert isinstance(prereqs, list)
                    
                    for prereq in prereqs:
                        assert isinstance(prereq, str)
                        assert len(prereq) > 0
        
        # Should prioritize paths
        if "prioritized_paths" in privesc_result:
            prioritized = privesc_result["prioritized_paths"]
            assert isinstance(prioritized, list)
            
            # Should be ordered by priority (highest first)
            for i in range(len(prioritized) - 1):
                current_score = prioritized[i].get("overall_score", 0)
                next_score = prioritized[i + 1].get("overall_score", 0)
                assert current_score >= next_score, "Paths should be ordered by score"


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_mitigation_recommendations(api_client: APIClient):
    """Test privilege escalation agent provides mitigation recommendations"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "privesc_mode": "defensive_analysis",
        "generate_mitigations": True,
        "prioritize_fixes": True,
        "inputs": {
            "targets": ["10.100.2.50"],
            "depth": "standard",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=250, interval=15)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    if len(privesc_results) > 0:
        privesc_result = privesc_results[0]
        
        # Should have mitigation recommendations
        if "mitigations" in privesc_result:
            mitigations = privesc_result["mitigations"]
            assert isinstance(mitigations, list)
            
            for mitigation in mitigations:
                assert "vulnerability" in mitigation
                assert "recommendation" in mitigation
                assert "priority" in mitigation
                
                assert mitigation["priority"] in ["critical", "high", "medium", "low"]
                assert len(mitigation["recommendation"]) > 20, "Recommendation should be detailed"
                
                if "implementation_difficulty" in mitigation:
                    assert mitigation["implementation_difficulty"] in ["easy", "medium", "hard"]
                
                if "estimated_effort" in mitigation:
                    assert isinstance(mitigation["estimated_effort"], str)
        
        # Should provide defensive recommendations
        if "defensive_recommendations" in privesc_result:
            defensive = privesc_result["defensive_recommendations"]
            
            # Common defensive categories
            defensive_categories = ["access_control", "monitoring", "hardening", "patching"]
            
            for category in defensive_categories:
                if category in defensive:
                    recommendations = defensive[category]
                    assert isinstance(recommendations, list)
                    
                    for rec in recommendations:
                        assert isinstance(rec, str)
                        assert len(rec) > 10


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_error_handling(api_client: APIClient):
    """Test privilege escalation agent handles errors and access restrictions"""
    # Test with highly restricted target
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "timeout_per_check": 10,
        "max_total_time": 120,
        "inputs": {
            "targets": ["169.254.169.254"],  # Link-local, should be restricted,
            "depth": "basic",
            "features": ["privesc"],
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
    
    await wait_for_condition(check_completed, timeout=150, interval=10)
    
    # Should handle gracefully
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] in ["completed", "failed"], "Should complete or fail gracefully"
    
    # Check results for error handling
    results = await api_client.get(f"/runs/{run_id}/results")
    privesc_results = [r for r in results["results"] if r["agent"] == "privesc"]
    
    if len(privesc_results) > 0:
        privesc_result = privesc_results[0]
        
        # Should handle access restrictions
        if "access_denied" in privesc_result:
            assert isinstance(privesc_result["access_denied"], int)
            assert privesc_result["access_denied"] >= 0
        
        # Should track timeout issues
        if "check_timeouts" in privesc_result:
            assert isinstance(privesc_result["check_timeouts"], int)
            assert privesc_result["check_timeouts"] >= 0


@pytest.mark.asyncio
@pytest.mark.privesc
async def test_privesc_agent_logging_to_opensearch(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test privilege escalation agent actions are logged to OpenSearch"""
    # Run a privilege escalation enumeration
    from src.utils import APIClient
    api_client = APIClient(test_config["api_base"])
    
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["privesc"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=120, interval=10)
    
    # Allow time for logging
    await asyncio.sleep(5)
    await opensearch_client.refresh_index(test_config["os_idx_actions"])
    
    # Search for privilege escalation agent actions
    query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "privesc")
        ]
    )
    
    docs = await opensearch_client.search(test_config["os_idx_actions"], query)
    assert docs["hits"]["total"]["value"] >= 1, "Should have privilege escalation agent action logged"
    
    # Validate privesc action document
    action_doc = docs["hits"]["hits"][0]["_source"]
    
    required_fields = ["run_id", "agent", "tool", "status", "started_at", "ended_at"]
    validate_response_schema(action_doc, required_fields)
    
    assert action_doc["agent"] == "privesc"
    assert action_doc["tool"] in ["bloodhound", "winpeas", "linpeas", "privilege_check", "custom"]
    assert action_doc["status"] in ["completed", "failed", "error"]
    
    # Should have privilege escalation-specific metadata
    if "techniques_checked" in action_doc:
        assert isinstance(action_doc["techniques_checked"], list)
    
    if "escalation_paths_found" in action_doc:
        assert isinstance(action_doc["escalation_paths_found"], int)
        assert action_doc["escalation_paths_found"] >= 0
