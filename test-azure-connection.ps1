# PowerShell Script: Test Azure OpenSearch Connection
# File: test-azure-connection.ps1

Write-Host "🔍 TESTING AZURE OPENSEARCH CONNECTION" -ForegroundColor Green
Write-Host "=====================================" -ForegroundColor Green

$azureUrl = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io:9200"
$localUrl = "http://localhost:9200"

# Test Azure connection
Write-Host "`n🌐 Testing Azure OpenSearch..." -ForegroundColor Cyan
try {
    $azureResponse = Invoke-RestMethod -Uri $azureUrl -Method GET -TimeoutSec 10
    Write-Host "✅ Azure OpenSearch connected successfully!" -ForegroundColor Green
    Write-Host "   Cluster: $($azureResponse.cluster_name)" -ForegroundColor White
    $azureConnected = $true
} catch {
    Write-Host "❌ Azure connection failed: $($_.Exception.Message)" -ForegroundColor Red
    $azureConnected = $false
}

# Test Local connection
Write-Host "`n🏠 Testing Local OpenSearch..." -ForegroundColor Cyan
try {
    $localResponse = Invoke-RestMethod -Uri $localUrl -Method GET -TimeoutSec 5
    Write-Host "✅ Local OpenSearch connected successfully!" -ForegroundColor Green
    Write-Host "   Cluster: $($localResponse.cluster_name)" -ForegroundColor White
    $localConnected = $true
} catch {
    Write-Host "❌ Local connection failed: $($_.Exception.Message)" -ForegroundColor Red
    $localConnected = $false
}

# Recommendation
Write-Host "`n📋 RECOMMENDATION:" -ForegroundColor Magenta
if ($azureConnected -and $localConnected) {
    Write-Host "✅ Both connections work - use dual posting" -ForegroundColor Green
} elseif ($azureConnected) {
    Write-Host "✅ Use Azure OpenSearch only" -ForegroundColor Green
} elseif ($localConnected) {
    Write-Host "✅ Use Local OpenSearch only" -ForegroundColor Green
    Write-Host "   Dashboard: http://localhost:5601" -ForegroundColor White
} else {
    Write-Host "❌ No OpenSearch connections available" -ForegroundColor Red
}

# Test data posting
if ($localConnected) {
    Write-Host "`n📤 Testing data post to local..." -ForegroundColor Cyan
    $testData = @{
        "timestamp" = Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ"
        "test_type" = "connection_test"
        "target_ip" = "127.0.0.1"
        "severity" = "info"
        "result" = "Connection test successful"
        "source" = "azure-connection-test"
    } | ConvertTo-Json

    try {
        $postUrl = "$localUrl/vulnerabilities/_doc"
        $headers = @{
            "Content-Type" = "application/json"
        }
        $response = Invoke-RestMethod -Uri $postUrl -Method POST -Body $testData -Headers $headers
        Write-Host "✅ Test data posted successfully!" -ForegroundColor Green
        Write-Host "   Document ID: $($response._id)" -ForegroundColor White
    } catch {
        Write-Host "❌ Data posting failed: $($_.Exception.Message)" -ForegroundColor Red
    }
}

Write-Host "`n🎯 NEXT STEPS:" -ForegroundColor Yellow
Write-Host "1. Open dashboard: http://localhost:5601" -ForegroundColor White
Write-Host "2. View data in Discover tab" -ForegroundColor White
Write-Host "3. Create visualizations" -ForegroundColor White
}
