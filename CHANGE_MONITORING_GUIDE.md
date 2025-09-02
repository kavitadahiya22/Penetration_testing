# 👁️ Real-Time Change Monitoring on Azure OpenSearch Dashboard

## 🌐 Dashboard URL
https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/app/home#/

## 🔍 Methods to View All Changes

### Method 1: Discover Tab - Live Data Monitoring
1. **Navigate to Discover Tab** (left sidebar)
2. **Set Time Range** to "Last 15 minutes" or "Auto-refresh"
3. **Enable Auto-Refresh**:
   - Click the time picker (top-right)
   - Toggle "Auto refresh" ON
   - Set interval: 10s, 30s, or 1m
4. **Sort by @timestamp desc** to see newest changes first
5. **Watch for new records** appearing in real-time

### Method 2: Create Real-Time Visualization
1. **Go to Visualize** → "Create visualization"
2. **Select "Line Chart"** or "Area Chart"
3. **Configure**:
   - Index: `vulnerabilities*`
   - X-axis: Date histogram on `@timestamp`
   - Y-axis: Count of documents
4. **Set Time Range**: "Last 1 hour" with auto-refresh
5. **Save** as "Vulnerability Activity Monitor"

### Method 3: Build Change Dashboard
1. **Go to Dashboard** → "Create new dashboard"
2. **Add Visualizations**:
   - Recent Activity Timeline
   - Severity Distribution (Pie Chart)
   - Test Type Breakdown (Bar Chart)
   - Target IP Activity (Heat Map)
3. **Enable Auto-Refresh** for the entire dashboard
4. **Save** as "Penetration Testing Monitor"

### Method 4: Dev Tools Live Monitoring
```json
GET vulnerabilities/_search
{
  "size": 10,
  "sort": [{"@timestamp": {"order": "desc"}}],
  "query": {
    "range": {
      "@timestamp": {
        "gte": "now-1h"
      }
    }
  }
}
```

### Method 5: PowerShell Live Monitoring Script
```powershell
# Real-time monitoring script
while ($true) {
    Clear-Host
    Write-Host "🔍 LIVE VULNERABILITY MONITORING 🔍" -ForegroundColor Cyan
    Write-Host "Time: $(Get-Date)" -ForegroundColor Yellow
    
    $recent = Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_search?size=5&sort=@timestamp:desc" -Method GET
    
    Write-Host "📊 Recent Activity (Last 5 records):" -ForegroundColor Green
    foreach ($hit in $recent.hits.hits) {
        $time = [DateTime]::Parse($hit._source.'@timestamp').ToString('HH:mm:ss')
        Write-Host "[$time] $($hit._source.severity) - $($hit._source.test_type)" -ForegroundColor White
    }
    
    Start-Sleep -Seconds 10
}
```

## 🎯 Dashboard Navigation for Changes

### Step-by-Step Change Tracking:

#### 1. **Index Pattern Setup** (One-time)
- Go to **Stack Management** → **Index Patterns**
- Create pattern: `vulnerabilities*`
- Time field: `@timestamp`

#### 2. **Discover Configuration**
- **Columns to add**:
  - `@timestamp`
  - `test_type`
  - `severity` 
  - `target_ip`
  - `result`
  - `workflow_status`

#### 3. **Time Range Settings**
- **Recent changes**: "Last 15 minutes"
- **Today's activity**: "Today"
- **Complete history**: "Last 7 days"

#### 4. **Filtering Options**
```
Filter by severity: severity:"critical" OR severity:"high"
Filter by type: test_type:"nmap_scan"
Filter by target: target_ip:"192.168.1.*"
Filter by status: workflow_status:"IMMORTAL"
```

## 📊 Advanced Change Detection

### Real-Time Queries for Specific Changes:

#### Latest Critical Issues:
```json
GET vulnerabilities/_search
{
  "size": 10,
  "sort": [{"@timestamp": {"order": "desc"}}],
  "query": {
    "bool": {
      "must": [
        {"terms": {"severity": ["critical", "high"]}},
        {"range": {"@timestamp": {"gte": "now-1h"}}}
      ]
    }
  }
}
```

#### New Scan Results:
```json
GET vulnerabilities/_search
{
  "size": 10,
  "sort": [{"@timestamp": {"order": "desc"}}],
  "query": {
    "bool": {
      "must": [
        {"wildcard": {"test_type": "*scan*"}},
        {"range": {"@timestamp": {"gte": "now-30m"}}}
      ]
    }
  }
}
```

#### Workflow Status Changes:
```json
GET vulnerabilities/_search
{
  "size": 10,
  "sort": [{"@timestamp": {"order": "desc"}}],
  "query": {
    "exists": {"field": "workflow_status"}
  }
}
```

## 🔔 Alert Setup (Optional)

### Create Alerting Rules:
1. **Go to Alerting** (if available)
2. **Create Monitor** for:
   - New critical vulnerabilities
   - High-frequency scan activity
   - System status changes
3. **Set Triggers**:
   - Document count > threshold
   - New severity levels detected
   - Workflow status changes

## 🎯 Quick Change Summary Commands

### PowerShell Quick Commands:
```powershell
# Load config
. .\azure-config.ps1

# Get latest 5 changes
$latest = Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_search?size=5&sort=@timestamp:desc" -Method GET

# Show changes in the last hour
$hourly = Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_search?q=@timestamp:[now-1h TO now]&sort=@timestamp:desc" -Method GET

# Count by severity (changes analysis)
$stats = Invoke-RestMethod -Uri "$Global:AzureAPI/vulnerabilities/_search?size=0&aggs={'severity_count':{'terms':{'field':'severity.keyword'}}}" -Method GET
```

## 🌟 Pro Tips for Change Monitoring

1. **Bookmark Queries**: Save frequently used searches
2. **Use Filters**: Create filter sets for common views
3. **Export Data**: Download change reports as CSV
4. **Share Dashboards**: Create team monitoring views
5. **Set Refresh Intervals**: Balance between real-time and performance

## 🚀 Your Current Data State
- **Total Records**: 9 vulnerability entries
- **Latest Activity**: SYSTEM_STATUS_REPORT (15:34:46 UTC)
- **Change Frequency**: ~32 minutes of activity logged
- **Update Pattern**: Real-time as new scans complete

Your penetration testing dashboard is ready for comprehensive change monitoring! 🎯
