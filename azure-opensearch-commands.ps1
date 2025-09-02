# Azure OpenSearch Quick Commands
# Save this file and run: .\azure-opensearch-commands.ps1

Write-Host "🌐 AZURE OPENSEARCH QUICK COMMANDS" -ForegroundColor Green
Write-Host "==================================" -ForegroundColor Green

# Azure OpenSearch URL
$azureUrl = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/"
$dashboardUrl = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io"

Write-Host "`n📋 Available Commands:" -ForegroundColor Cyan
Write-Host "1. test      - Test connection" -ForegroundColor White
Write-Host "2. post      - Post sample data" -ForegroundColor White
Write-Host "3. dashboard - Open dashboard" -ForegroundColor White
Write-Host "4. help      - Show this menu" -ForegroundColor White
Write-Host "`nUsage: .\azure-opensearch-commands.ps1 [command]" -ForegroundColor Yellow

param(
    [string]$Command = "help"
)

switch ($Command.ToLower()) {
    "test" {
        Write-Host "`n🔌 Testing Azure OpenSearch connection..." -ForegroundColor Cyan
        try {
            $response = Invoke-RestMethod -Uri $azureUrl -Method GET -TimeoutSec 15
            Write-Host "✅ Connected successfully!" -ForegroundColor Green
            Write-Host "   Cluster: $($response.cluster_name)" -ForegroundColor White
            Write-Host "   Version: $($response.version.number)" -ForegroundColor White
        } catch {
            Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "post" {
        Write-Host "`n📤 Posting test data to Azure OpenSearch..." -ForegroundColor Cyan
        $data = @{
            "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
            "test_type" = "quick_command_test"
            "target_ip" = "example.com"
            "severity" = "info"
            "result" = "Test data from PowerShell quick command"
            "source" = "azure-commands-script"
        } | ConvertTo-Json
        
        try {
            $postUrl = "$azureUrl/vulnerabilities/_doc"
            $response = Invoke-RestMethod -Uri $postUrl -Method POST -Body $data -ContentType "application/json" -TimeoutSec 15
            Write-Host "✅ Data posted successfully!" -ForegroundColor Green
            Write-Host "   Document ID: $($response._id)" -ForegroundColor White
        } catch {
            Write-Host "❌ Posting failed: $($_.Exception.Message)" -ForegroundColor Red
        }
    }
    
    "dashboard" {
        Write-Host "`n🎯 Opening Azure OpenSearch Dashboard..." -ForegroundColor Cyan
        try {
            Start-Process $dashboardUrl
            Write-Host "✅ Dashboard opened in browser!" -ForegroundColor Green
            Write-Host "   URL: $dashboardUrl" -ForegroundColor White
        } catch {
            Write-Host "❌ Failed to open dashboard: $($_.Exception.Message)" -ForegroundColor Red
            Write-Host "   Please manually open: $dashboardUrl" -ForegroundColor Yellow
        }
    }
    
    default {
        Write-Host "`n💡 Examples:" -ForegroundColor Yellow
        Write-Host "   .\azure-opensearch-commands.ps1 test" -ForegroundColor Gray
        Write-Host "   .\azure-opensearch-commands.ps1 post" -ForegroundColor Gray
        Write-Host "   .\azure-opensearch-commands.ps1 dashboard" -ForegroundColor Gray
        Write-Host "`n🔗 Endpoints:" -ForegroundColor Cyan
        Write-Host "   API: $azureUrl" -ForegroundColor White
        Write-Host "   Dashboard: $dashboardUrl" -ForegroundColor White
    }
}
