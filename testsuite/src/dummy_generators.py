"""
Test data generators for cybrty-pentest testing
Generate realistic but safe test data for penetration testing scenarios
"""
import random
import string
import ipaddress
from typing import List, Dict, Any, Optional
from datetime import datetime, timezone, timedelta


class NetworkTargetGenerator:
    """Generate network targets for testing"""
    
    SAFE_NETWORKS = [
        "127.0.0.0/8",    # Loopback
        "10.0.0.0/8",     # RFC1918 Private
        "172.16.0.0/12",  # RFC1918 Private
        "192.168.0.0/16", # RFC1918 Private
        "169.254.0.0/16", # Link-local
    ]
    
    @staticmethod
    def generate_safe_ip() -> str:
        """Generate a safe IP address for testing"""
        networks = [
            ipaddress.IPv4Network("127.0.0.0/8"),
            ipaddress.IPv4Network("10.0.0.0/8"),
            ipaddress.IPv4Network("192.168.0.0/16")
        ]
        
        network = random.choice(networks)
        # Generate random host in network
        host_bits = 32 - network.prefixlen
        max_hosts = min(2**host_bits - 2, 1000)  # Limit for safety
        host_num = random.randint(1, max_hosts)
        
        return str(network.network_address + host_num)
    
    @staticmethod
    def generate_safe_network(max_hosts: int = 256) -> str:
        """Generate a safe network range for testing"""
        base_networks = ["10.0.0.0", "192.168.0.0", "172.16.0.0"]
        base = random.choice(base_networks)
        
        # Calculate prefix length based on max hosts
        if max_hosts <= 2:
            prefix = 30
        elif max_hosts <= 6:
            prefix = 29
        elif max_hosts <= 14:
            prefix = 28
        elif max_hosts <= 30:
            prefix = 27
        elif max_hosts <= 62:
            prefix = 26
        elif max_hosts <= 126:
            prefix = 25
        elif max_hosts <= 254:
            prefix = 24
        else:
            prefix = 24
        
        return f"{base}/{prefix}"
    
    @staticmethod
    def generate_target_list(count: int = 5) -> List[str]:
        """Generate list of mixed safe targets"""
        targets = []
        
        for _ in range(count):
            target_type = random.choice(["ip", "network", "domain", "url"])
            
            if target_type == "ip":
                targets.append(NetworkTargetGenerator.generate_safe_ip())
            elif target_type == "network":
                targets.append(NetworkTargetGenerator.generate_safe_network())
            elif target_type == "domain":
                targets.append(DomainGenerator.generate_test_domain())
            elif target_type == "url":
                targets.append(URLGenerator.generate_test_url())
        
        return targets


class DomainGenerator:
    """Generate test domain names"""
    
    TEST_TLDS = [".test", ".local", ".example", ".localhost"]
    COMMON_SUBDOMAINS = ["www", "api", "admin", "mail", "ftp", "dev", "staging"]
    
    @staticmethod
    def generate_test_domain() -> str:
        """Generate a safe test domain"""
        company_names = [
            "testcorp", "democorp", "example", "testsite", "demoapp",
            "safecorp", "testlab", "mocksite", "samplecorp", "testenv"
        ]
        
        company = random.choice(company_names)
        tld = random.choice(DomainGenerator.TEST_TLDS)
        
        # Optionally add subdomain
        if random.choice([True, False]):
            subdomain = random.choice(DomainGenerator.COMMON_SUBDOMAINS)
            return f"{subdomain}.{company}{tld}"
        
        return f"{company}{tld}"
    
    @staticmethod
    def generate_domain_list(count: int = 3) -> List[str]:
        """Generate list of test domains"""
        return [DomainGenerator.generate_test_domain() for _ in range(count)]


class URLGenerator:
    """Generate test URLs"""
    
    @staticmethod
    def generate_test_url(scheme: str = "http") -> str:
        """Generate a safe test URL"""
        domain = DomainGenerator.generate_test_domain()
        
        paths = [
            "/", "/admin", "/login", "/api/v1", "/dashboard", 
            "/user/profile", "/search", "/files", "/api/users"
        ]
        
        path = random.choice(paths)
        port = random.choice(["", ":8080", ":3000", ":8443", ":8090"])
        
        return f"{scheme}://{domain}{port}{path}"
    
    @staticmethod
    def generate_url_list(count: int = 5) -> List[str]:
        """Generate list of test URLs"""
        urls = []
        for _ in range(count):
            scheme = random.choice(["http", "https"])
            urls.append(URLGenerator.generate_test_url(scheme))
        return urls


class CredentialGenerator:
    """Generate test credentials"""
    
    COMMON_USERNAMES = [
        "admin", "administrator", "root", "user", "guest", "test",
        "demo", "service", "backup", "oracle", "postgres", "mysql"
    ]
    
    COMMON_PASSWORDS = [
        "admin", "password", "123456", "admin123", "root", "toor",
        "test", "demo", "guest", "service", "P@ssw0rd", "Welcome123"
    ]
    
    SERVICES = ["http", "ssh", "ftp", "telnet", "rdp", "smb", "mysql", "postgresql"]
    
    @staticmethod
    def generate_credential_pair() -> Dict[str, str]:
        """Generate a username/password pair"""
        return {
            "username": random.choice(CredentialGenerator.COMMON_USERNAMES),
            "password": random.choice(CredentialGenerator.COMMON_PASSWORDS),
            "service": random.choice(CredentialGenerator.SERVICES)
        }
    
    @staticmethod
    def generate_credential_list(count: int = 10) -> List[Dict[str, str]]:
        """Generate list of credential pairs"""
        return [CredentialGenerator.generate_credential_pair() for _ in range(count)]
    
    @staticmethod
    def generate_weak_password() -> str:
        """Generate an obviously weak password"""
        weak_patterns = [
            "password123", "admin123", "123456", "qwerty", "letmein",
            "welcome", "monkey", "dragon", "master", "shadow"
        ]
        return random.choice(weak_patterns)


class VulnerabilityGenerator:
    """Generate test vulnerability data"""
    
    CVE_PREFIXES = ["CVE-2023-", "CVE-2024-", "CVE-2025-"]
    
    VULNERABILITY_TYPES = [
        "SQL Injection", "Cross-Site Scripting (XSS)", "Cross-Site Request Forgery (CSRF)",
        "Remote Code Execution", "Buffer Overflow", "Authentication Bypass",
        "Directory Traversal", "Information Disclosure", "Denial of Service",
        "Privilege Escalation", "Insecure Direct Object Reference", "Security Misconfiguration"
    ]
    
    SEVERITY_LEVELS = ["Critical", "High", "Medium", "Low", "Informational"]
    
    @staticmethod
    def generate_cve_id() -> str:
        """Generate a fake CVE ID"""
        prefix = random.choice(VulnerabilityGenerator.CVE_PREFIXES)
        number = random.randint(1000, 9999)
        return f"{prefix}{number}"
    
    @staticmethod
    def generate_vulnerability() -> Dict[str, Any]:
        """Generate a test vulnerability"""
        return {
            "id": VulnerabilityGenerator.generate_cve_id(),
            "name": random.choice(VulnerabilityGenerator.VULNERABILITY_TYPES),
            "severity": random.choice(VulnerabilityGenerator.SEVERITY_LEVELS),
            "description": "Test vulnerability for penetration testing validation",
            "affected_service": random.choice(["Apache", "Nginx", "MySQL", "SSH", "FTP", "SMB"]),
            "port": random.choice([22, 80, 443, 21, 3306, 139, 445]),
            "cvss_score": round(random.uniform(1.0, 10.0), 1),
            "exploitable": random.choice([True, False]),
            "remediation": "Apply security patches and follow best practices"
        }
    
    @staticmethod
    def generate_vulnerability_list(count: int = 5) -> List[Dict[str, Any]]:
        """Generate list of test vulnerabilities"""
        return [VulnerabilityGenerator.generate_vulnerability() for _ in range(count)]


class BloodHoundDataGenerator:
    """Generate test BloodHound/Active Directory data"""
    
    @staticmethod
    def generate_test_domain() -> str:
        """Generate test domain name"""
        domains = ["TESTLAB.LOCAL", "DEMO.LOCAL", "EXAMPLE.COM", "CORP.LOCAL"]
        return random.choice(domains)
    
    @staticmethod
    def generate_computer_name(domain: str) -> str:
        """Generate computer name"""
        prefixes = ["DC", "WS", "SRV", "PC", "LAP"]
        numbers = random.randint(1, 99)
        return f"{random.choice(prefixes)}{numbers:02d}.{domain}"
    
    @staticmethod
    def generate_user_name(domain: str) -> str:
        """Generate user name"""
        first_names = ["John", "Jane", "Admin", "Service", "Test", "Demo"]
        last_names = ["Doe", "Smith", "Johnson", "User", "Account", "Service"]
        
        first = random.choice(first_names)
        last = random.choice(last_names)
        
        return f"{first.upper()}.{last.upper()}@{domain}"
    
    @staticmethod
    def generate_group_name(domain: str) -> str:
        """Generate group name"""
        groups = [
            "Domain Admins", "Enterprise Admins", "Schema Admins",
            "Remote Desktop Users", "Backup Operators", "Account Operators"
        ]
        return f"{random.choice(groups).upper()}@{domain}"
    
    @staticmethod
    def generate_bloodhound_data() -> Dict[str, Any]:
        """Generate minimal BloodHound test data"""
        domain = BloodHoundDataGenerator.generate_test_domain()
        
        # Generate computers
        computers = []
        for i in range(random.randint(2, 5)):
            computer = {
                "Name": BloodHoundDataGenerator.generate_computer_name(domain),
                "Properties": {
                    "domain": domain,
                    "highvalue": i == 0,  # First computer is high value (DC)
                    "enabled": True,
                    "haslaps": random.choice([True, False])
                },
                "LocalAdmins": [],
                "Sessions": []
            }
            computers.append(computer)
        
        # Generate users
        users = []
        for i in range(random.randint(3, 8)):
            user = {
                "Name": BloodHoundDataGenerator.generate_user_name(domain),
                "Properties": {
                    "domain": domain,
                    "highvalue": i == 0,  # First user is high value (admin)
                    "enabled": True,
                    "admincount": i == 0
                }
            }
            users.append(user)
        
        # Generate groups
        groups = []
        for i in range(random.randint(2, 4)):
            group = {
                "Name": BloodHoundDataGenerator.generate_group_name(domain),
                "Properties": {
                    "domain": domain,
                    "highvalue": "ADMIN" in group["Name"],
                    "admincount": "ADMIN" in group["Name"]
                },
                "Members": []
            }
            groups.append(group)
        
        return {
            "computers": computers,
            "users": users,
            "groups": groups,
            "meta": {
                "type": "domains",
                "count": 1,
                "version": 4
            }
        }


class PortScanGenerator:
    """Generate realistic port scan results"""
    
    COMMON_PORTS = [
        {"port": 22, "service": "ssh", "state": "open"},
        {"port": 80, "service": "http", "state": "open"},
        {"port": 443, "service": "https", "state": "open"},
        {"port": 21, "service": "ftp", "state": "closed"},
        {"port": 23, "service": "telnet", "state": "filtered"},
        {"port": 25, "service": "smtp", "state": "open"},
        {"port": 53, "service": "dns", "state": "open"},
        {"port": 110, "service": "pop3", "state": "closed"},
        {"port": 143, "service": "imap", "state": "open"},
        {"port": 993, "service": "imaps", "state": "open"},
        {"port": 995, "service": "pop3s", "state": "closed"},
        {"port": 139, "service": "netbios-ssn", "state": "open"},
        {"port": 445, "service": "microsoft-ds", "state": "open"},
        {"port": 3389, "service": "rdp", "state": "open"},
        {"port": 3306, "service": "mysql", "state": "closed"},
        {"port": 5432, "service": "postgresql", "state": "closed"},
        {"port": 1433, "service": "mssql", "state": "closed"},
        {"port": 8080, "service": "http-alt", "state": "open"},
        {"port": 8443, "service": "https-alt", "state": "open"}
    ]
    
    @staticmethod
    def generate_port_scan_result(target: str) -> Dict[str, Any]:
        """Generate realistic port scan results"""
        # Select random subset of ports
        num_ports = random.randint(5, 12)
        scanned_ports = random.sample(PortScanGenerator.COMMON_PORTS, num_ports)
        
        # Randomize some states
        for port in scanned_ports:
            if random.random() < 0.2:  # 20% chance to change state
                port["state"] = random.choice(["open", "closed", "filtered"])
        
        open_ports = [p for p in scanned_ports if p["state"] == "open"]
        
        return {
            "target": target,
            "scan_time": round(random.uniform(5.0, 30.0), 2),
            "hosts_up": 1 if open_ports else 0,
            "total_hosts": 1,
            "ports_scanned": len(scanned_ports),
            "open_ports": len(open_ports),
            "services": scanned_ports,
            "os_detection": {
                "os_family": random.choice(["Linux", "Windows", "Unknown"]),
                "confidence": random.randint(50, 95)
            }
        }


class TestScenarioGenerator:
    """Generate complete test scenarios"""
    
    @staticmethod
    def generate_recon_scenario() -> Dict[str, Any]:
        """Generate reconnaissance test scenario"""
        targets = NetworkTargetGenerator.generate_target_list(3)
        return {
            "name": f"recon-scenario-{random.randint(1000, 9999)}",
            "targets": targets,
            "depth": random.choice(["basic", "standard"]),
            "features": ["recon"],
            "simulate": True,
            "expected_tools": ["nmap", "amass"],
            "expected_duration": random.randint(60, 300)
        }
    
    @staticmethod
    def generate_web_scenario() -> Dict[str, Any]:
        """Generate web security test scenario"""
        urls = URLGenerator.generate_url_list(2)
        return {
            "name": f"web-scenario-{random.randint(1000, 9999)}",
            "targets": urls,
            "depth": random.choice(["standard", "advanced"]),
            "features": ["web", "vuln"],
            "simulate": True,
            "expected_tools": ["zap", "nikto", "sqlmap"],
            "expected_duration": random.randint(120, 600)
        }
    
    @staticmethod
    def generate_full_pentest_scenario() -> Dict[str, Any]:
        """Generate full penetration test scenario"""
        targets = NetworkTargetGenerator.generate_target_list(2)
        targets.extend(URLGenerator.generate_url_list(1))
        
        return {
            "name": f"full-pentest-{random.randint(1000, 9999)}",
            "targets": targets,
            "depth": "comprehensive",
            "features": ["recon", "web", "vuln", "creds", "lateral", "priv-esc"],
            "simulate": True,
            "expected_tools": ["nmap", "amass", "zap", "nikto", "sqlmap", "hydra", "cme", "bloodhound"],
            "expected_duration": random.randint(600, 1800)
        }


def generate_test_tenant_id() -> str:
    """Generate test tenant ID"""
    return f"test-tenant-{random.randint(100, 999)}"


def generate_test_run_id() -> str:
    """Generate test run ID"""
    chars = string.ascii_lowercase + string.digits
    return f"run-{''.join(random.choices(chars, k=8))}"


def generate_test_plan_id() -> str:
    """Generate test plan ID"""
    chars = string.ascii_lowercase + string.digits
    return f"plan-{''.join(random.choices(chars, k=8))}"


def generate_timestamp(offset_minutes: int = 0) -> str:
    """Generate ISO timestamp with optional offset"""
    dt = datetime.now(timezone.utc) + timedelta(minutes=offset_minutes)
    return dt.isoformat().replace("+00:00", "Z")
