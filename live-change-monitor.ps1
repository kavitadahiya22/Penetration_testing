# 🔍 Live Azure OpenSearch Change Monitor

Write-Host "🚀 STARTING LIVE CHANGE MONITOR 🚀" -ForegroundColor Cyan
Write-Host "Dashboard: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/app/home#/" -ForegroundColor Yellow
Write-Host "Press Ctrl+C to stop monitoring" -ForegroundColor White
Write-Host "════════════════════════════════════════════════════" -ForegroundColor Yellow

# Load Azure configuration
. .\azure-config.ps1

$lastRecordCount = 0
$monitoringStart = Get-Date

while ($true) {
    try {
        Clear-Host
        Write-Host "👁️ LIVE VULNERABILITY CHANGE MONITOR 👁️" -ForegroundColor Cyan
        Write-Host "════════════════════════════════════════════════════" -ForegroundColor Yellow
        Write-Host "🕐 Current Time: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss UTC')" -ForegroundColor White
        Write-Host "⏰ Monitoring Since: $($monitoringStart.ToString('HH:mm:ss'))" -ForegroundColor Gray
        Write-Host "🌐 Dashboard: https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/app/home#/" -ForegroundColor Magenta
        Write-Host ""

        # Get current record count
        $countResult = Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_search" -Method GET -Body '{"size":0}' -ContentType "application/json"
        $currentCount = $countResult.hits.total.value

        # Check for changes
        if ($currentCount -ne $lastRecordCount) {
            if ($lastRecordCount -gt 0) {
                $newRecords = $currentCount - $lastRecordCount
                Write-Host "🚨 CHANGE DETECTED! +$newRecords new records" -ForegroundColor Red
                # Play system beep for changes (optional)
                # [System.Console]::Beep(800, 200)
            }
            $lastRecordCount = $currentCount
        }

        Write-Host "📊 CURRENT STATUS:" -ForegroundColor Green
        Write-Host "   Total Records: $currentCount" -ForegroundColor White
        Write-Host ""

        # Get latest 5 records
        $searchBody = @{
            size = 5
            sort = @(@{
                "@timestamp" = @{
                    order = "desc"
                }
            })
        } | ConvertTo-Json -Depth 3
        
        $recentData = Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_search" -Method POST -Body $searchBody -ContentType "application/json"
        
        Write-Host "🔥 LATEST ACTIVITY (Last 5 Records):" -ForegroundColor Green
        Write-Host "────────────────────────────────────────────────────" -ForegroundColor Gray
        
        $counter = 1
        foreach ($hit in $recentData.hits.hits) {
            $timestamp = [DateTime]::Parse($hit._source.'@timestamp').ToString('HH:mm:ss')
            $severity = $hit._source.severity.ToUpper()
            $testType = $hit._source.test_type
            $target = $hit._source.target_ip
            
            # Color code by severity
            $severityColor = switch ($severity) {
                "CRITICAL" { "Red" }
                "HIGH" { "Yellow" }
                "MEDIUM" { "Cyan" }
                "SUCCESS" { "Green" }
                default { "White" }
            }
            
            Write-Host "$counter. [$timestamp] " -NoNewline -ForegroundColor Gray
            Write-Host "[$severity] " -NoNewline -ForegroundColor $severityColor
            Write-Host "$testType → $target" -ForegroundColor White
            $counter++
        }

        Write-Host ""
        Write-Host "🔄 Next refresh in 10 seconds..." -ForegroundColor Gray
        Write-Host "════════════════════════════════════════════════════" -ForegroundColor Yellow
        
        # Wait 10 seconds
        Start-Sleep -Seconds 10
        
    } catch {
        Write-Host "❌ Error monitoring changes: $($_.Exception.Message)" -ForegroundColor Red
        Write-Host "🔄 Retrying in 15 seconds..." -ForegroundColor Yellow
        Start-Sleep -Seconds 15
    }
}
