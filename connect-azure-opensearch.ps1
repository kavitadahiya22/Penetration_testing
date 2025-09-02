# PowerShell Script: Connect to Azure OpenSearch
# File: connect-azure-opensearch.ps1

Write-Host "🌐 AZURE OPENSEARCH CONNECTION SCRIPT" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

# Azure OpenSearch Configuration
$azureOpenSearchUrl = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/"
$azureDashboardUrl = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io"

Write-Host "`n📋 Configuration:" -ForegroundColor Cyan
Write-Host "OpenSearch API: $azureOpenSearchUrl" -ForegroundColor White
Write-Host "Dashboard URL: $azureDashboardUrl" -ForegroundColor White

# Function to test OpenSearch connection
function Test-AzureOpenSearch {
    Write-Host "`n🔌 Testing Azure OpenSearch connection..." -ForegroundColor Cyan
    
    try {
        $response = Invoke-RestMethod -Uri $azureOpenSearchUrl -Method GET -TimeoutSec 15
        Write-Host "✅ Successfully connected to Azure OpenSearch!" -ForegroundColor Green
        Write-Host "   Cluster: $($response.cluster_name)" -ForegroundColor White
        Write-Host "   Version: $($response.version.number)" -ForegroundColor White
        return $true
    } catch {
        Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to post data to Azure OpenSearch
function Post-DataToAzure {
    param(
        [string]$TestType = "connection_test",
        [string]$TargetIp = "127.0.0.1",
        [string]$Severity = "info",
        [string]$Result = "Azure connection test"
    )
    
    Write-Host "`n📤 Posting test data to Azure..." -ForegroundColor Cyan
    
    $data = @{
        "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
        "test_type" = $TestType
        "target_ip" = $TargetIp
        "severity" = $Severity
        "result" = $Result
        "source" = "azure-opensearch-script"
        "environment" = "production"
    } | ConvertTo-Json
    
    try {
        $postUrl = "$azureOpenSearchUrl/vulnerabilities/_doc"
        $headers = @{
            "Content-Type" = "application/json"
        }
        
        $response = Invoke-RestMethod -Uri $postUrl -Method POST -Body $data -Headers $headers -TimeoutSec 15
        Write-Host "✅ Data posted successfully!" -ForegroundColor Green
        Write-Host "   Document ID: $($response._id)" -ForegroundColor White
        Write-Host "   Index: $($response._index)" -ForegroundColor White
        return $true
    } catch {
        Write-Host "❌ Data posting failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

# Function to open Azure Dashboard
function Open-AzureDashboard {
    Write-Host "`n🎯 Opening Azure OpenSearch Dashboard..." -ForegroundColor Cyan
    Write-Host "URL: $azureDashboardUrl" -ForegroundColor White
    
    try {
        Start-Process $azureDashboardUrl
        Write-Host "✅ Dashboard opened in browser!" -ForegroundColor Green
    } catch {
        Write-Host "❌ Failed to open dashboard: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "   Please manually open: $azureDashboardUrl" -ForegroundColor Yellow
    }
}

# Main execution
Write-Host "`n🚀 Starting Azure OpenSearch connection..." -ForegroundColor Yellow

# Test connection
$connected = Test-AzureOpenSearch

if ($connected) {
    # Post test data
    $dataPosted = Post-DataToAzure -TestType "azure_endpoint_test" -Result "Successfully connected to Azure OpenSearch with /es/ endpoint"
    
    # Open dashboard
    Open-AzureDashboard
    
    Write-Host "`n🎉 SUCCESS! Azure OpenSearch is connected and ready!" -ForegroundColor Green
    Write-Host "`n📋 Next steps:" -ForegroundColor Magenta
    Write-Host "1. Check the Azure dashboard for your data" -ForegroundColor White
    Write-Host "2. Use the API endpoint: $azureOpenSearchUrl" -ForegroundColor White
    Write-Host "3. Configure your application to use these endpoints" -ForegroundColor White
    
} else {
    Write-Host "`n⚠️  Connection failed. Please check:" -ForegroundColor Yellow
    Write-Host "1. Network connectivity" -ForegroundColor White
    Write-Host "2. Azure Container Apps status" -ForegroundColor White
    Write-Host "3. OpenSearch service availability" -ForegroundColor White
}

Write-Host "`n🔗 Azure Endpoints:" -ForegroundColor Cyan
Write-Host "OpenSearch API: $azureOpenSearchUrl" -ForegroundColor White
Write-Host "Dashboard: $azureDashboardUrl" -ForegroundColor White
