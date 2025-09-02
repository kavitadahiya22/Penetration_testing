# Azure OpenSearch Quick Reference
# Your verified configuration details

Write-Host "🔧 AZURE OPENSEARCH CONFIGURATION" -ForegroundColor Green
Write-Host "=================================" -ForegroundColor Green
Write-Host ""
Write-Host "Cluster Name: docker-cluster" -ForegroundColor Cyan
Write-Host "Version: 3.1.0 (OpenSearch)" -ForegroundColor Cyan  
Write-Host "Node: cybrty-dev-ca--v1-6cc66fd748-b5dxv" -ForegroundColor Cyan
Write-Host "API Endpoint: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/" -ForegroundColor Yellow
Write-Host "Dashboard: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io" -ForegroundColor Yellow
Write-Host ""

# Set global variables
$Global:AzureAPI = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/"
$Global:AzureDashboard = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io"

Write-Host "📋 READY-TO-USE COMMANDS:" -ForegroundColor Magenta
Write-Host "=========================" -ForegroundColor Magenta
Write-Host ""
Write-Host "1. TEST CONNECTION:" -ForegroundColor Yellow
Write-Host '   Invoke-RestMethod -Uri $Global:AzureAPI -Method GET' -ForegroundColor Gray
Write-Host ""
Write-Host "2. POST VULNERABILITY DATA:" -ForegroundColor Yellow  
Write-Host '   $data = @{' -ForegroundColor Gray
Write-Host '       "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"' -ForegroundColor Gray
Write-Host '       "test_type" = "port_scan"' -ForegroundColor Gray
Write-Host '       "target_ip" = "192.168.1.100"' -ForegroundColor Gray
Write-Host '       "severity" = "high"' -ForegroundColor Gray
Write-Host '       "result" = "Open SSH port found"' -ForegroundColor Gray
Write-Host '   } | ConvertTo-Json' -ForegroundColor Gray
Write-Host '   Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_doc" -Method POST -Body $data -ContentType "application/json"' -ForegroundColor Gray
Write-Host ""
Write-Host "3. OPEN DASHBOARD:" -ForegroundColor Yellow
Write-Host '   Start-Process $Global:AzureDashboard' -ForegroundColor Gray
Write-Host ""
Write-Host "✅ All variables are set and ready to use!" -ForegroundColor Green
