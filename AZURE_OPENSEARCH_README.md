# Azure OpenSearch - Penetration Testing Integration
# Quick Reference Card

## VERIFIED CONFIGURATION ✅
```
Cluster Name: docker-cluster
Version: 3.1.0 (OpenSearch)
Node: cybrty-dev-ca--v1-6cc66fd748-b5dxv
API Endpoint: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/
Dashboard: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io
Status: ✅ OPERATIONAL
```

## POWERSHELL COMMANDS

### Load Configuration
```powershell
. .\azure-config.ps1
```

### Test Connection
```powershell
Invoke-RestMethod -Uri $Global:AzureAPI -Method GET
```

### Post Vulnerability Data
```powershell
$data = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "port_scan"
    "target_ip" = "192.168.1.100"
    "severity" = "high"
    "result" = "Open SSH port found"
    "port" = 22
    "service" = "SSH"
} | ConvertTo-Json

Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_doc" -Method POST -Body $data -ContentType "application/json"
```

### Open Dashboard
```powershell
Start-Process $Global:AzureDashboard
```

## PENETRATION TESTING EXAMPLES

### Nmap Scan Results
```powershell
$nmapData = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "nmap_scan"
    "target_ip" = "10.0.0.1"
    "severity" = "info"
    "result" = "Network discovery completed"
    "open_ports" = @(22, 80, 443)
    "tool" = "nmap"
} | ConvertTo-Json
```

### Vulnerability Assessment
```powershell
$vulnData = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "vulnerability_scan"
    "target_ip" = "192.168.1.50"
    "severity" = "critical"
    "result" = "SQL injection vulnerability found"
    "cve" = "CVE-2023-1234"
    "url" = "http://192.168.1.50/login.php"
} | ConvertTo-Json
```

### Web Application Test
```powershell
$webData = @{
    "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
    "test_type" = "web_app_test"
    "target_ip" = "192.168.1.100"
    "severity" = "medium"
    "result" = "Cross-site scripting (XSS) detected"
    "url" = "http://192.168.1.100/search?q=<script>"
    "method" = "GET"
} | ConvertTo-Json
```

## FILES CREATED ✅
- `azure-opensearch-config.json` - JSON configuration
- `azure-config.ps1` - PowerShell configuration script
- `azure-opensearch-functions.ps1` - Advanced functions (needs fixing)
- `AZURE_OPENSEARCH_README.md` - This reference guide

## NEXT STEPS
1. Use `.\azure-config.ps1` to load variables
2. Test connection with your commands
3. Start posting real penetration testing data
4. Monitor results in the Azure dashboard
5. Integrate with your existing pentest tools

## TROUBLESHOOTING
- Connection issues: Check `Invoke-RestMethod -Uri $Global:AzureAPI -Method GET`
- Posting issues: Verify JSON format and ContentType
- Dashboard access: Use `Start-Process $Global:AzureDashboard`
