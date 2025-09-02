# Simple Azure OpenSearch Test Script
Write-Host "🌐 TESTING AZURE OPENSEARCH" -ForegroundColor Green
Write-Host "===========================" -ForegroundColor Green

# Test connection
$url = "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/"
Write-Host "`nTesting connection to: $url" -ForegroundColor Cyan

try {
    $response = Invoke-RestMethod -Uri $url -Method GET -TimeoutSec 15
    Write-Host "✅ SUCCESS! Connected to Azure OpenSearch" -ForegroundColor Green
    Write-Host "Cluster: $($response.cluster_name)" -ForegroundColor Yellow
    Write-Host "Version: $($response.version.number)" -ForegroundColor Yellow
    
    # Test data posting
    Write-Host "`n📤 Testing data posting..." -ForegroundColor Cyan
    $data = '{"@timestamp":"' + (Get-Date -Format "yyyy-MM-ddTHH:mm:ss.fffZ") + '","test_type":"connection_test","target_ip":"test.example.com","severity":"info","result":"Azure connection successful"}'
    
    $postUrl = "$url/vulnerabilities/_doc"
    $postResponse = Invoke-RestMethod -Uri $postUrl -Method POST -Body $data -ContentType "application/json" -TimeoutSec 15
    Write-Host "✅ Data posted successfully!" -ForegroundColor Green
    Write-Host "Document ID: $($postResponse._id)" -ForegroundColor Yellow
    
} catch {
    Write-Host "❌ Error: $($_.Exception.Message)" -ForegroundColor Red
}

Write-Host "`n🎯 Dashboard URL:" -ForegroundColor Cyan
Write-Host "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io" -ForegroundColor White
