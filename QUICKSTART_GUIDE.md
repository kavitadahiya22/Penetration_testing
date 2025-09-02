# Azure OpenSearch Penetration Testing - Quick Start Guide

## ✅ WORKFLOW VERIFIED AND WORKING

Your Azure OpenSearch integration has been successfully tested with the following workflow:

### 🚀 COMPLETE WORKING COMMANDS

```powershell
# 1. Load configuration (already done)
. .\azure-config.ps1

# 2. Test your connection  
Invoke-RestMethod -Uri $Global:AzureAPI -Method GET

# 3. Post penetration testing data
$data = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "nmap_scan" 
    "target_ip" = "192.168.1.100"
    "severity" = "high"
    "result" = "Critical vulnerability found"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_doc" -Method POST -Body $data -ContentType "application/json"
```

### 📊 VERIFIED CONFIGURATION

```
Cluster Name: docker-cluster
Version: 3.1.0 (OpenSearch)  
Node: cybrty-dev-ca--v1-6cc66fd748-b5dxv
API Endpoint: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/
Dashboard: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io
Status: 🟢 OPERATIONAL
```

### 🔒 PENETRATION TESTING DATA EXAMPLES

#### Nmap Port Scan
```powershell
$nmapData = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "port_scan"
    "target_ip" = "192.168.1.50"
    "severity" = "medium"
    "result" = "Open ports: 22, 80, 443, 3389"
    "ports" = @(22, 80, 443, 3389)
    "tool" = "nmap"
} | ConvertTo-Json
```

#### Vulnerability Assessment
```powershell
$vulnData = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "vulnerability_scan"
    "target_ip" = "10.0.0.100"
    "severity" = "critical"
    "result" = "SQL injection vulnerability detected"
    "cve" = "CVE-2023-1234"
    "cvss_score" = 9.8
    "port" = 80
    "service" = "HTTP"
} | ConvertTo-Json
```

#### Web Application Test
```powershell
$webAppData = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "web_app_test"
    "target_ip" = "203.0.113.50"
    "severity" = "high"
    "result" = "Cross-site scripting (XSS) vulnerability found"
    "url" = "https://example.com/search"
    "method" = "GET"
    "payload" = "<script>alert('XSS')</script>"
} | ConvertTo-Json
```

### 🎯 PRODUCTION USAGE

1. **Run your penetration tests** using your preferred tools
2. **Format the results** using the data structure examples above
3. **Post to Azure OpenSearch** using the verified commands
4. **Monitor results** in the Azure OpenSearch Dashboard
5. **Generate reports** from the centralized vulnerability data

### 📁 AVAILABLE FILES

- `azure-config.ps1` - Quick configuration loader
- `azure-pentest-integration.ps1` - Complete integration script
- `azure-opensearch-config.json` - JSON configuration
- `AZURE_OPENSEARCH_README.md` - Complete documentation

### 🌐 ACCESS POINTS

- **API Endpoint**: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/
- **Dashboard**: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io

## 🎉 SUCCESS!

Your Azure OpenSearch penetration testing platform is fully operational and ready for production use!
