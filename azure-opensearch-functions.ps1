# Azure OpenSearch PowerShell Functions
# Source: . .\azure-opensearch-functions.ps1

# Azure OpenSearch Configuration
$Global:AzureOpenSearchConfig = @{
    ClusterName = "docker-cluster"
    Version = "3.1.0"
    Node = "cybrty-dev-ca--v1-6cc66fd748-b5dxv"
    ApiEndpoint = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/"
    Dashboard = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io"
    Timeout = 15
}

function Test-AzureOpenSearch {
    <#
    .SYNOPSIS
    Test connection to Azure OpenSearch cluster
    #>
    Write-Host "🔌 Testing Azure OpenSearch Connection..." -ForegroundColor Cyan
    Write-Host "Cluster: $($Global:AzureOpenSearchConfig.ClusterName)" -ForegroundColor White
    
    try {
        $response = Invoke-RestMethod -Uri $Global:AzureOpenSearchConfig.ApiEndpoint -Method GET -TimeoutSec $Global:AzureOpenSearchConfig.Timeout
        Write-Host "✅ Connection successful!" -ForegroundColor Green
        Write-Host "  Node: $($response.name)" -ForegroundColor Yellow
        Write-Host "  Version: $($response.version.number)" -ForegroundColor Yellow
        return $true
    } catch {
        Write-Host "❌ Connection failed: $($_.Exception.Message)" -ForegroundColor Red
        return $false
    }
}

function Post-VulnerabilityData {
    <#
    .SYNOPSIS
    Post vulnerability data to Azure OpenSearch
    .PARAMETER TestType
    Type of test performed
    .PARAMETER TargetIp
    Target IP address
    .PARAMETER Severity
    Severity level (low, medium, high, critical)
    .PARAMETER Result
    Test result description
    .PARAMETER Port
    Target port (optional)
    .PARAMETER Service
    Service name (optional)
    #>
    param(
        [Parameter(Mandatory=$true)]
        [string]$TestType,
        
        [Parameter(Mandatory=$true)]
        [string]$TargetIp,
        
        [Parameter(Mandatory=$true)]
        [ValidateSet("low", "medium", "high", "critical", "info")]
        [string]$Severity,
        
        [Parameter(Mandatory=$true)]
        [string]$Result,
        
        [Parameter(Mandatory=$false)]
        [int]$Port,
        
        [Parameter(Mandatory=$false)]
        [string]$Service
    )
    
    Write-Host "📤 Posting vulnerability data to Azure..." -ForegroundColor Cyan
    
    $data = @{
        "@timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
        "test_type" = $TestType
        "target_ip" = $TargetIp
        "severity" = $Severity
        "result" = $Result
        "source" = "pentest_powershell"
        "cluster" = $Global:AzureOpenSearchConfig.ClusterName
    }
    
    if ($Port) { $data["port"] = $Port }
    if ($Service) { $data["service"] = $Service }
    
    $jsonData = $data | ConvertTo-Json
    
    try {
        $postUrl = $Global:AzureOpenSearchConfig.ApiEndpoint + "vulnerabilities/_doc"
        $response = Invoke-RestMethod -Uri $postUrl -Method POST -Body $jsonData -ContentType "application/json" -TimeoutSec $Global:AzureOpenSearchConfig.Timeout
        
        Write-Host "✅ Data posted successfully!" -ForegroundColor Green
        Write-Host "  Document ID: $($response._id)" -ForegroundColor Yellow
        Write-Host "  Index: $($response._index)" -ForegroundColor Yellow
        
        return $response._id
    } catch {
        Write-Host "❌ Posting failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Get-ClusterHealth {
    <#
    .SYNOPSIS
    Get Azure OpenSearch cluster health
    #>
    Write-Host "🏥 Checking cluster health..." -ForegroundColor Cyan
    
    try {
        $healthUrl = $Global:AzureOpenSearchConfig.ApiEndpoint + "_cluster/health"
        $health = Invoke-RestMethod -Uri $healthUrl -Method GET -TimeoutSec $Global:AzureOpenSearchConfig.Timeout
        
        $statusColor = switch ($health.status) {
            "green" { "Green" }
            "yellow" { "Yellow" }
            "red" { "Red" }
            default { "White" }
        }
        
        Write-Host "✅ Cluster Health: $($health.status.ToUpper())" -ForegroundColor $statusColor
        Write-Host "  Active Shards: $($health.active_shards)" -ForegroundColor White
        Write-Host "  Nodes: $($health.number_of_nodes)" -ForegroundColor White
        
        return $health
    } catch {
        Write-Host "❌ Health check failed: $($_.Exception.Message)" -ForegroundColor Red
        return $null
    }
}

function Open-AzureDashboard {
    <#
    .SYNOPSIS
    Open Azure OpenSearch Dashboard in browser
    #>
    Write-Host "🎯 Opening Azure OpenSearch Dashboard..." -ForegroundColor Cyan
    try {
        Start-Process $Global:AzureOpenSearchConfig.Dashboard
        Write-Host "✅ Dashboard opened!" -ForegroundColor Green
        Write-Host "  URL: $($Global:AzureOpenSearchConfig.Dashboard)" -ForegroundColor White
    } catch {
        Write-Host "❌ Failed to open dashboard" -ForegroundColor Red
        Write-Host "  Manual URL: $($Global:AzureOpenSearchConfig.Dashboard)" -ForegroundColor Yellow
    }
}

function Show-AzureConfig {
    <#
    .SYNOPSIS
    Display current Azure OpenSearch configuration
    #>
    Write-Host "🔧 AZURE OPENSEARCH CONFIGURATION" -ForegroundColor Green
    Write-Host "=================================" -ForegroundColor Green
    Write-Host ""
    Write-Host "Cluster Name: $($Global:AzureOpenSearchConfig.ClusterName)" -ForegroundColor Cyan
    Write-Host "Version: $($Global:AzureOpenSearchConfig.Version)" -ForegroundColor Cyan
    Write-Host "Node: $($Global:AzureOpenSearchConfig.Node)" -ForegroundColor Cyan
    Write-Host "API Endpoint: $($Global:AzureOpenSearchConfig.ApiEndpoint)" -ForegroundColor Yellow
    Write-Host "Dashboard: $($Global:AzureOpenSearchConfig.Dashboard)" -ForegroundColor Yellow
    Write-Host "Timeout: $($Global:AzureOpenSearchConfig.Timeout) seconds" -ForegroundColor White
}

# Display available functions
Write-Host "🚀 AZURE OPENSEARCH FUNCTIONS LOADED" -ForegroundColor Green
Write-Host "====================================" -ForegroundColor Green
Write-Host ""
Write-Host "Available Functions:" -ForegroundColor Cyan
Write-Host "• Test-AzureOpenSearch" -ForegroundColor White
Write-Host "• Post-VulnerabilityData" -ForegroundColor White
Write-Host "• Get-ClusterHealth" -ForegroundColor White
Write-Host "• Open-AzureDashboard" -ForegroundColor White
Write-Host "• Show-AzureConfig" -ForegroundColor White
Write-Host ""
Write-Host "Usage Example:" -ForegroundColor Yellow
Write-Host 'Post-VulnerabilityData -TestType "port_scan" -TargetIp "192.168.1.100" -Severity "high" -Result "Open SSH port found" -Port 22 -Service "SSH"' -ForegroundColor Gray
