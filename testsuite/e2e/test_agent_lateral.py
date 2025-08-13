"""
Tests for the Lateral Movement Agent
Validates BloodHound/CME integration, network enumeration, privilege discovery, and movement safety
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.utils import APIClient, validate_response_schema, DataManager
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.lateral
@pytest.mark.smoke
async def test_lateral_agent_basic_enumeration(api_client: APIClient):
    """Test lateral movement agent performs basic network enumeration"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "enumeration_only",
        "max_depth": 1,
        "inputs": {
            "targets": ["10.0.0.100"],
            "depth": "basic",
            "features": ["lateral"],
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
    
    # Should have lateral movement results
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    assert len(lateral_results) > 0, "Should have lateral movement agent results"
    
    # Validate lateral result structure
    lateral_result = lateral_results[0]
    required_fields = ["agent", "target", "network_hosts", "enumeration_type"]
    validate_response_schema(lateral_result, required_fields)
    
    assert lateral_result["agent"] == "lateral"
    assert lateral_result["enumeration_type"] in ["network_scan", "smb_enum", "ldap_enum"]
    assert isinstance(lateral_result["network_hosts"], list)


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_bloodhound_integration(api_client: APIClient):
    """Test lateral movement agent integrates with BloodHound"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "ad_enumeration",
        "use_bloodhound": True,
        "domain_context": True,
        "inputs": {
            "targets": ["172.16.1.100"],
            "depth": "advanced",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    assert len(lateral_results) > 0, "Should have lateral movement results"
    
    # Validate BloodHound integration
    lateral_result = lateral_results[0]
    
    if "tools_used" in lateral_result:
        tools = [tool.lower() for tool in lateral_result["tools_used"]]
        assert any("bloodhound" in tool for tool in tools), "Should use BloodHound"
    
    # Should have Active Directory enumeration results
    if "ad_objects" in lateral_result:
        ad_objects = lateral_result["ad_objects"]
        assert isinstance(ad_objects, dict)
        
        # Common BloodHound object types
        ad_types = ["users", "computers", "groups", "domains"]
        found_types = [t for t in ad_types if t in ad_objects]
        assert len(found_types) >= 1, "Should enumerate AD objects"
        
        for obj_type in found_types:
            assert isinstance(ad_objects[obj_type], (list, int))
    
    # Should have privilege paths
    if "privilege_paths" in lateral_result:
        paths = lateral_result["privilege_paths"]
        assert isinstance(paths, list)
        
        for path in paths:
            if "source" in path and "target" in path:
                assert "relationship" in path
                assert path["relationship"] in [
                    "AdminTo", "MemberOf", "HasSession", "CanRDP", 
                    "ExecuteDCOM", "AllowedToDelegate"
                ]


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_cme_integration(api_client: APIClient):
    """Test lateral movement agent integrates with CrackMapExec for SMB enumeration"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "smb_enumeration",
        "use_cme": True,
        "enumerate_shares": True,
        "enumerate_sessions": True,
        "inputs": {
            "targets": ["10.10.1.200"],
            "depth": "standard",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Check CME integration
        if "tools_used" in lateral_result:
            tools = [tool.lower() for tool in lateral_result["tools_used"]]
            assert any("cme" in tool or "crackmapexec" in tool for tool in tools), \
                "Should use CrackMapExec"
        
        # Should have SMB enumeration results
        if "smb_hosts" in lateral_result:
            smb_hosts = lateral_result["smb_hosts"]
            assert isinstance(smb_hosts, list)
            
            for host in smb_hosts:
                if "shares" in host:
                    assert isinstance(host["shares"], list)
                
                if "sessions" in host:
                    assert isinstance(host["sessions"], list)
                
                if "signing" in host:
                    assert isinstance(host["signing"], bool)
        
        # Should identify potential movement targets
        if "movement_targets" in lateral_result:
            targets = lateral_result["movement_targets"]
            assert isinstance(targets, list)
            
            for target in targets:
                assert "host" in target
                assert "access_method" in target
                assert target["access_method"] in [
                    "smb", "winrm", "rdp", "psexec", "wmiexec"
                ]


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_network_discovery(api_client: APIClient):
    """Test lateral movement agent discovers network topology"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "network_discovery",
        "subnet_enumeration": True,
        "service_discovery": True,
        "trust_relationships": True,
        "inputs": {
            "targets": ["192.168.10.50"],
            "depth": "comprehensive",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should discover network topology
        if "network_topology" in lateral_result:
            topology = lateral_result["network_topology"]
            assert isinstance(topology, dict)
            
            if "subnets" in topology:
                subnets = topology["subnets"]
                assert isinstance(subnets, list)
                
                for subnet in subnets:
                    assert "network" in subnet
                    assert "hosts_alive" in subnet
                    assert isinstance(subnet["hosts_alive"], int)
        
        # Should identify services across network
        if "network_services" in lateral_result:
            services = lateral_result["network_services"]
            assert isinstance(services, dict)
            
            # Common services for lateral movement
            lateral_services = ["smb", "winrm", "rdp", "ssh", "wmi"]
            found_services = [s for s in lateral_services if s in services]
            # Should find some lateral movement services
        
        # Should map trust relationships
        if "trust_relationships" in lateral_result:
            trusts = lateral_result["trust_relationships"]
            assert isinstance(trusts, list)
            
            for trust in trusts:
                if "source_domain" in trust and "target_domain" in trust:
                    assert "trust_type" in trust
                    assert trust["trust_type"] in [
                        "parent_child", "external", "forest", "shortcut"
                    ]


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_privilege_escalation_paths(api_client: APIClient):
    """Test lateral movement agent identifies privilege escalation opportunities"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "privilege_paths",
        "identify_escalation": True,
        "map_admin_access": True,
        "check_delegations": True,
        "inputs": {
            "targets": ["10.50.1.100"],
            "depth": "advanced",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should identify escalation paths
        if "escalation_paths" in lateral_result:
            paths = lateral_result["escalation_paths"]
            assert isinstance(paths, list)
            
            for path in paths:
                assert "current_user" in path
                assert "target_user" in path
                assert "method" in path
                assert "complexity" in path
                
                assert path["complexity"] in ["low", "medium", "high"]
                assert path["method"] in [
                    "group_membership", "delegation", "service_account",
                    "admin_session", "kerberoasting", "asreproasting"
                ]
        
        # Should map administrative access
        if "admin_access" in lateral_result:
            admin_access = lateral_result["admin_access"]
            assert isinstance(admin_access, list)
            
            for access in admin_access:
                assert "user" in access
                assert "target" in access
                assert "access_type" in access
                
                assert access["access_type"] in [
                    "local_admin", "domain_admin", "enterprise_admin",
                    "service_admin", "dcom_access"
                ]
        
        # Should check dangerous delegations
        if "delegations" in lateral_result:
            delegations = lateral_result["delegations"]
            assert isinstance(delegations, list)
            
            for delegation in delegations:
                if "type" in delegation:
                    assert delegation["type"] in [
                        "unconstrained", "constrained", "resource_based"
                    ]
                
                if "risk_level" in delegation:
                    assert delegation["risk_level"] in ["critical", "high", "medium", "low"]


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_movement_safety(api_client: APIClient):
    """Test lateral movement agent respects safety constraints"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "safe_enumeration",
        "no_actual_movement": True,
        "read_only_operations": True,
        "avoid_detection": True,
        "production_target": True,
        "inputs": {
            "targets": ["172.20.1.50"],
            "depth": "basic",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should not perform actual movement
        assert lateral_result.get("movement_attempted", False) == False, \
            "Should not attempt actual lateral movement"
        
        # Should use only read-only operations
        if "operations_performed" in lateral_result:
            operations = lateral_result["operations_performed"]
            
            # Should not contain write operations
            dangerous_ops = ["write", "execute", "modify", "delete", "create"]
            for op in operations:
                assert not any(danger in op.lower() for danger in dangerous_ops), \
                    f"Found dangerous operation: {op}"
        
        # Should implement stealth measures
        if "stealth_measures" in lateral_result:
            stealth = lateral_result["stealth_measures"]
            assert isinstance(stealth, list)
            assert len(stealth) > 0, "Should implement stealth measures"
        
        # Should be production-safe
        if "production_safe" in lateral_result:
            assert lateral_result["production_safe"] == True


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_kerberos_analysis(api_client: APIClient):
    """Test lateral movement agent analyzes Kerberos vulnerabilities"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "kerberos_analysis",
        "check_kerberoasting": True,
        "check_asreproasting": True,
        "check_delegations": True,
        "inputs": {
            "targets": ["10.100.1.200"],
            "depth": "advanced",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should analyze Kerberos vulnerabilities
        if "kerberos_analysis" in lateral_result:
            kerberos = lateral_result["kerberos_analysis"]
            assert isinstance(kerberos, dict)
            
            # Kerberoasting opportunities
            if "kerberoastable_accounts" in kerberos:
                accounts = kerberos["kerberoastable_accounts"]
                assert isinstance(accounts, list)
                
                for account in accounts:
                    assert "samaccountname" in account
                    if "spn" in account:
                        assert isinstance(account["spn"], list)
            
            # ASREPRoasting opportunities
            if "asreproastable_accounts" in kerberos:
                asrep_accounts = kerberos["asreproastable_accounts"]
                assert isinstance(asrep_accounts, list)
                
                for account in asrep_accounts:
                    assert "dont_require_preauth" in account
                    assert account["dont_require_preauth"] == True
            
            # Delegation vulnerabilities
            if "delegation_vulnerabilities" in kerberos:
                delegations = kerberos["delegation_vulnerabilities"]
                assert isinstance(delegations, list)
                
                for delegation in delegations:
                    assert "account" in delegation
                    assert "delegation_type" in delegation
                    assert delegation["delegation_type"] in [
                        "unconstrained", "constrained", "resource_based"
                    ]


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_session_enumeration(api_client: APIClient):
    """Test lateral movement agent enumerates user sessions"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "lateral_mode": "session_enumeration",
        "enumerate_logged_users": True,
        "map_user_sessions": True,
        "inputs": {
            "targets": ["192.168.20.100"],
            "depth": "standard",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should enumerate user sessions
        if "user_sessions" in lateral_result:
            sessions = lateral_result["user_sessions"]
            assert isinstance(sessions, list)
            
            for session in sessions:
                assert "host" in session
                assert "user" in session
                
                if "session_type" in session:
                    assert session["session_type"] in [
                        "interactive", "rdp", "service", "network"
                    ]
                
                if "privileges" in session:
                    assert isinstance(session["privileges"], list)
        
        # Should map privileged sessions
        if "privileged_sessions" in lateral_result:
            priv_sessions = lateral_result["privileged_sessions"]
            assert isinstance(priv_sessions, list)
            
            for session in priv_sessions:
                assert "privilege_level" in session
                assert session["privilege_level"] in [
                    "domain_admin", "local_admin", "enterprise_admin", "service_admin"
                ]


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_error_handling(api_client: APIClient):
    """Test lateral movement agent handles errors and access denials"""
    # Test with restricted target
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "timeout_per_operation": 10,
        "max_total_time": 120,
        "inputs": {
            "targets": ["127.0.0.1"],  # Localhost with limited access,
            "depth": "basic",
            "features": ["lateral"],
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
    lateral_results = [r for r in results["results"] if r["agent"] == "lateral"]
    
    if len(lateral_results) > 0:
        lateral_result = lateral_results[0]
        
        # Should handle access denials
        if "access_denied" in lateral_result:
            assert isinstance(lateral_result["access_denied"], int)
            assert lateral_result["access_denied"] >= 0
        
        # Should track timeout issues
        if "timeouts" in lateral_result:
            assert isinstance(lateral_result["timeouts"], int)
            assert lateral_result["timeouts"] >= 0


@pytest.mark.asyncio
@pytest.mark.lateral
async def test_lateral_agent_logging_to_opensearch(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test lateral movement agent actions are logged to OpenSearch"""
    # Run a lateral movement enumeration
    from src.utils import APIClient
    api_client = APIClient(test_config["api_base"])
    
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["lateral"],
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
    
    # Search for lateral movement agent actions
    query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "lateral")
        ]
    )
    
    docs = await opensearch_client.search(test_config["os_idx_actions"], query)
    assert docs["hits"]["total"]["value"] >= 1, "Should have lateral movement agent action logged"
    
    # Validate lateral action document
    action_doc = docs["hits"]["hits"][0]["_source"]
    
    required_fields = ["run_id", "agent", "tool", "status", "started_at", "ended_at"]
    validate_response_schema(action_doc, required_fields)
    
    assert action_doc["agent"] == "lateral"
    assert action_doc["tool"] in ["bloodhound", "cme", "crackmapexec", "nmap", "enum4linux"]
    assert action_doc["status"] in ["completed", "failed", "error"]
    
    # Should have lateral-specific metadata
    if "enumeration_type" in action_doc:
        assert action_doc["enumeration_type"] in [
            "network", "smb", "ldap", "kerberos", "sessions"
        ]
    
    if "hosts_enumerated" in action_doc:
        assert isinstance(action_doc["hosts_enumerated"], int)
        assert action_doc["hosts_enumerated"] >= 0
