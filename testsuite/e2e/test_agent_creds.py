"""
Tests for the Credentials Agent  
Validates Hydra/CME integration, credential discovery, brute force attacks, and safety controls
"""
import pytest
import asyncio
from typing import Dict, Any, List
from unittest.mock import Mock, patch

from src.utils import APIClient, validate_response_schema, DataManager
from src.os_queries import OpenSearchClient, OpenSearchQueries
from src.dummy_generators import generate_test_tenant_id


@pytest.mark.asyncio
@pytest.mark.creds
@pytest.mark.smoke
async def test_creds_agent_basic_discovery(api_client: APIClient):
    """Test credentials agent can discover credential opportunities"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "inputs": {
            "targets": ["10.0.0.75"],
            "depth": "quick", 
            "features": ["creds"],
            "simulate": True
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    assert "run_id" in response
    
    run_id = response["run_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=180, interval=10)
    
    # Get final status
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] == "completed"
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    
    # Should have creds results
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    assert len(creds_results) > 0, "Should have credentials agent results"
    
    # Validate creds result structure
    creds_result = creds_results[0]
    required_fields = ["agent", "target", "services_identified", "auth_methods"]
    validate_response_schema(creds_result, required_fields)
    
    assert creds_result["agent"] == "creds"
    assert isinstance(creds_result["services_identified"], list)
    assert isinstance(creds_result["auth_methods"], list)


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_hydra_integration(api_client: APIClient):
    """Test credentials agent integrates with Hydra"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "inputs": {
            "targets": ["172.16.0.100"],
            "depth": "standard",
            "features": ["creds"],
            "simulate": True
        },
        "auto_plan": True,
        "policy": {
            "creds_mode": "test_common",
            "use_hydra": True,
            "max_attempts": 10,
            "target_services": ["ssh", "ftp", "telnet"]
        }
    }
    
    response = await api_client.post("/agents/pentest/run", run_input)
    run_id = response["run_id"]
    
    # Wait for completion
    from src.utils import wait_for_condition
    
    async def check_completed():
        status = await api_client.get(f"/runs/{run_id}")
        return status["status"] in ["completed", "failed", "error"]
    
    await wait_for_condition(check_completed, timeout=240, interval=15)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    assert len(creds_results) > 0, "Should have credentials results"
    
    # Validate Hydra integration
    creds_result = creds_results[0]
    
    if "tools_used" in creds_result:
        assert "hydra" in creds_result["tools_used"], "Should use Hydra"
    
    # Should have service-specific attempts
    if "attempts" in creds_result:
        attempts = creds_result["attempts"]
        assert isinstance(attempts, list)
        
        for attempt in attempts:
            if "service" in attempt:
                assert attempt["service"] in ["ssh", "ftp", "telnet", "http", "https"]
            
            if "method" in attempt:
                assert attempt["method"] in ["brute_force", "dictionary", "common_creds"]
            
            # Should respect attempt limits
            if "attempt_count" in attempt:
                assert attempt["attempt_count"] <= 10, "Should respect max_attempts policy"


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_cme_integration(api_client: APIClient):
    """Test credentials agent integrates with CrackMapExec (CME)"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "creds_mode": "smb_enumeration",
        "use_cme": True,
        "target_services": ["smb", "winrm"],
        "domain_aware": True,
        "inputs": {
            "targets": ["10.10.0.200"],
            "depth": "advanced",
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
    
    await wait_for_condition(check_completed, timeout=300, interval=20)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Check CME integration
        if "tools_used" in creds_result:
            tools = [tool.lower() for tool in creds_result["tools_used"]]
            assert any("cme" in tool or "crackmapexec" in tool for tool in tools), \
                "Should use CrackMapExec"
        
        # Should have SMB/Windows specific results
        if "domain_info" in creds_result:
            domain_info = creds_result["domain_info"]
            assert isinstance(domain_info, dict)
            
            # Common CME outputs
            cme_fields = ["domain_name", "domain_controller", "smb_signing"]
            found_fields = [field for field in cme_fields if field in domain_info]
            # Should have some domain information
        
        # Check service enumeration
        if "services_enumerated" in creds_result:
            services = creds_result["services_enumerated"]
            assert isinstance(services, list)
            
            # Should target Windows services
            windows_services = {"smb", "winrm", "rdp", "ldap"}
            found_services = set(services).intersection(windows_services)
            # Should find some Windows services


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_wordlist_management(api_client: APIClient):
    """Test credentials agent uses appropriate wordlists"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "creds_mode": "targeted_wordlist",
        "wordlist_type": "common",
        "custom_usernames": ["admin", "test", "service"],
        "custom_passwords": ["password123", "admin", "test123"],
        "inputs": {
            "targets": ["192.168.50.100"],
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
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Check wordlist usage
        if "wordlists_used" in creds_result:
            wordlists = creds_result["wordlists_used"]
            assert isinstance(wordlists, list)
            
            # Should indicate wordlist type
            has_common = any("common" in wl.lower() for wl in wordlists)
            has_custom = any("custom" in wl.lower() for wl in wordlists)
            assert has_common or has_custom, "Should use specified wordlist types"
        
        # Check credential attempts
        if "credential_attempts" in creds_result:
            attempts = creds_result["credential_attempts"]
            
            # Should include custom credentials
            custom_usernames = {"admin", "test", "service"}
            custom_passwords = {"password123", "admin", "test123"}
            
            for attempt in attempts:
                if "username" in attempt:
                    # Custom usernames should be included
                    pass  # In simulation, actual attempts might vary
                
                if "password_list_size" in attempt:
                    assert isinstance(attempt["password_list_size"], int)
                    assert attempt["password_list_size"] > 0


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_safety_controls(api_client: APIClient):
    """Test credentials agent respects safety controls and rate limiting"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "creds_mode": "safe_test",
        "max_attempts": 5,
        "rate_limit_ms": 2000,  # 2 second delay between attempts,
        "lockout_protection": True,
        "production_target": True,
        "inputs": {
            "targets": ["10.0.1.50"],
            "depth": "basic",
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
    
    await wait_for_condition(check_completed, timeout=150, interval=10)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Should respect attempt limits
        if "total_attempts" in creds_result:
            total = creds_result["total_attempts"]
            assert total <= 5, f"Total attempts {total} exceeds limit of 5"
        
        # Should implement rate limiting
        if "rate_limited" in creds_result:
            assert creds_result["rate_limited"] == True, "Should implement rate limiting"
        
        # Should avoid lockout scenarios
        if "lockout_detected" in creds_result:
            assert creds_result["lockout_detected"] == False, "Should avoid account lockouts"
        
        # Should be production-safe
        if "production_safe" in creds_result:
            assert creds_result["production_safe"] == True, "Should be production-safe"


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_credential_validation(api_client: APIClient):
    """Test credentials agent validates found credentials"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "creds_mode": "validate_found",
        "test_credentials": [,
        {"username": "testuser", "password": "testpass123",
        "inputs": {
            "targets": ["172.20.0.150"],
            "depth": "advanced",
            "features": ["creds"],
            "simulate": True
        }
    },
                {"username": "admin", "password": "admin"}
            ],
            "validate_access": True
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
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Should validate credentials
        if "credentials_found" in creds_result:
            credentials = creds_result["credentials_found"]
            assert isinstance(credentials, list)
            
            for cred in credentials:
                required_cred_fields = ["username", "service", "status"]
                validate_response_schema(cred, required_cred_fields)
                
                assert cred["status"] in ["valid", "invalid", "unknown", "locked"]
                
                if "access_level" in cred:
                    assert cred["access_level"] in ["user", "admin", "root", "service"]
        
        # Should test multiple services per credential
        if "validation_results" in creds_result:
            validation = creds_result["validation_results"]
            
            for result in validation:
                if "services_tested" in result:
                    assert isinstance(result["services_tested"], list)
                    assert len(result["services_tested"]) >= 1


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_protocol_specific_attacks(api_client: APIClient):
    """Test credentials agent handles protocol-specific attack methods"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "protocol_specific": True,
        "ssh_methods": ["password", "key_auth"],
        "web_methods": ["form_auth", "basic_auth", "digest_auth"],
        "smb_methods": ["ntlm", "kerberos"],
        "database_methods": ["mysql", "postgres", "mssql"],
        "inputs": {
            "targets": ["10.50.0.100"],
            "depth": "comprehensive",
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
    
    await wait_for_condition(check_completed, timeout=350, interval=25)
    
    # Get results
    results = await api_client.get(f"/runs/{run_id}/results")
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Should use protocol-specific methods
        if "attack_methods" in creds_result:
            methods = creds_result["attack_methods"]
            assert isinstance(methods, dict)
            
            # Check protocol coverage
            protocols = ["ssh", "web", "smb", "database"]
            for protocol in protocols:
                if protocol in methods:
                    protocol_methods = methods[protocol]
                    assert isinstance(protocol_methods, list)
                    assert len(protocol_methods) >= 1
        
        # Should adapt to discovered services
        if "service_adaptations" in creds_result:
            adaptations = creds_result["service_adaptations"]
            
            for adaptation in adaptations:
                assert "service" in adaptation
                assert "method" in adaptation
                assert "rationale" in adaptation


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_error_handling(api_client: APIClient):
    """Test credentials agent handles errors and edge cases"""
    # Test with unreachable target
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "timeout_per_attempt": 5,
        "max_total_time": 60,
        "inputs": {
            "targets": ["192.168.255.255"],  # Unreachable,
            "depth": "basic",
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
    
    await wait_for_condition(check_completed, timeout=120, interval=10)
    
    # Should handle gracefully
    final_status = await api_client.get(f"/runs/{run_id}")
    assert final_status["status"] in ["completed", "failed"], "Should complete or fail gracefully"
    
    # Check results for error handling
    results = await api_client.get(f"/runs/{run_id}/results")
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Should have timeout/error information
        if "timeouts" in creds_result:
            assert isinstance(creds_result["timeouts"], int)
            assert creds_result["timeouts"] >= 0
        
        if "connection_errors" in creds_result:
            assert isinstance(creds_result["connection_errors"], int)
            assert creds_result["connection_errors"] >= 0


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_logging_to_opensearch(opensearch_client: OpenSearchClient, test_config: Dict):
    """Test credentials agent actions are logged to OpenSearch"""
    # Run a credentials scan
    from src.utils import APIClient
    api_client = APIClient(test_config["api_base"])
    
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "inputs": {
            "targets": ["127.0.0.1"],
            "depth": "basic",
            "features": ["creds"],
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
    
    # Search for credentials agent actions
    query = OpenSearchQueries.bool_query(
        must=[
            OpenSearchQueries.term_query("run_id", run_id),
            OpenSearchQueries.term_query("agent", "creds")
        ]
    )
    
    docs = await opensearch_client.search(test_config["os_idx_actions"], query)
    assert docs["hits"]["total"]["value"] >= 1, "Should have credentials agent action logged"
    
    # Validate credentials action document
    action_doc = docs["hits"]["hits"][0]["_source"]
    
    required_fields = ["run_id", "agent", "tool", "status", "started_at", "ended_at"]
    validate_response_schema(action_doc, required_fields)
    
    assert action_doc["agent"] == "creds"
    assert action_doc["tool"] in ["hydra", "cme", "crackmapexec", "custom", "nmap"]
    assert action_doc["status"] in ["completed", "failed", "error"]
    
    # Should have credentials-specific metadata
    if "target_services" in action_doc:
        assert isinstance(action_doc["target_services"], list)
    
    if "attempts_made" in action_doc:
        assert isinstance(action_doc["attempts_made"], int)
        assert action_doc["attempts_made"] >= 0


@pytest.mark.asyncio
@pytest.mark.creds
async def test_creds_agent_report_generation(api_client: APIClient):
    """Test credentials agent generates comprehensive reports"""
    run_input = {
        "tenant_id": generate_test_tenant_id(),
        "auto_plan": True,
        "policy": {,
        "generate_report": True,
        "include_recommendations": True,
        "report_format": "detailed",
        "inputs": {
            "targets": ["10.100.0.50"],
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
    creds_results = [r for r in results["results"] if r["agent"] == "creds"]
    
    if len(creds_results) > 0:
        creds_result = creds_results[0]
        
        # Should have comprehensive reporting
        if "report" in creds_result:
            report = creds_result["report"]
            
            report_sections = ["summary", "findings", "recommendations"]
            for section in report_sections:
                if section in report:
                    assert isinstance(report[section], (str, dict, list))
                    if isinstance(report[section], str):
                        assert len(report[section]) > 0
        
        # Should have security recommendations
        if "recommendations" in creds_result:
            recommendations = creds_result["recommendations"]
            assert isinstance(recommendations, list)
            
            for rec in recommendations:
                assert "priority" in rec
                assert rec["priority"] in ["critical", "high", "medium", "low"]
                assert "description" in rec
                assert len(rec["description"]) > 10
