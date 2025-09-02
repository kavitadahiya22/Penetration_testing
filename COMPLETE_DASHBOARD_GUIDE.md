# 👁️ Complete Guide: View All Changes on Azure OpenSearch Dashboard

## 🌐 Dashboard URL
**https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/app/home#/**

## 🎯 METHOD 1: Discover Tab (Recommended for Beginners)

### Step-by-Step Instructions:

1. **Navigate to Discover**
   - Click "Discover" in the left sidebar
   - This is your main data exploration tool

2. **Create Index Pattern** (One-time setup)
   - If prompted, click "Create index pattern"
   - Enter: `vulnerabilities*`
   - Click "Next step"
   - Select `@timestamp` as time field
   - Click "Create index pattern"

3. **View All Your Data**
   - You'll see all 9 vulnerability records
   - Data is automatically sorted by timestamp (newest first)
   - Each row shows your vulnerability scan results

4. **Customize Columns**
   - Click the gear icon ⚙️ to add/remove columns
   - Recommended columns:
     - `@timestamp` (time of scan)
     - `test_type` (type of security test)
     - `severity` (critical, high, medium, info)
     - `target_ip` (target system)
     - `result` (scan findings)
     - `workflow_status` (if present)

## 🎯 METHOD 2: Real-Time Auto-Refresh

### Enable Live Updates:
1. **In Discover Tab:**
   - Look for time picker (top-right, shows date range)
   - Click the time picker
   - Toggle "Auto refresh" ON
   - Set interval: 30 seconds or 1 minute
   - Set time range to "Last 24 hours"

2. **Watch Changes Live:**
   - New vulnerability scans will appear automatically
   - Page refreshes at your chosen interval
   - No need to manually reload

## 🎯 METHOD 3: Dev Tools (Advanced Users)

### Direct Query Interface:
1. **Go to Dev Tools**
   - Click "Dev Tools" in left sidebar
   - This opens the query console

2. **View All Records:**
   ```json
   GET vulnerabilities/_search
   {
     "size": 20,
     "sort": [
       {
         "@timestamp": {
           "order": "desc"
         }
       }
     ]
   }
   ```

3. **Filter by Severity:**
   ```json
   GET vulnerabilities/_search
   {
     "query": {
       "terms": {
         "severity": ["critical", "high"]
       }
     },
     "sort": [{"@timestamp": {"order": "desc"}}]
   }
   ```

## 🎯 METHOD 4: Create Custom Dashboard

### Build Your Monitoring Dashboard:

1. **Go to Dashboard Tab**
   - Click "Dashboard" in left sidebar
   - Click "Create new dashboard"

2. **Add Visualizations:**
   
   **A. Timeline Chart:**
   - Add visualization → Line chart
   - X-axis: Date histogram on `@timestamp`
   - Y-axis: Count of documents
   - Shows activity over time

   **B. Severity Breakdown:**
   - Add visualization → Pie chart
   - Split slices: Terms on `severity.keyword`
   - Shows distribution of vulnerability levels

   **C. Test Type Analysis:**
   - Add visualization → Bar chart
   - X-axis: Terms on `test_type.keyword`
   - Y-axis: Count
   - Shows which scan types are most active

   **D. Recent Activity Table:**
   - Add visualization → Data table
   - Rows: Terms on `@timestamp`
   - Columns: `test_type`, `severity`, `target_ip`

3. **Save Dashboard**
   - Click "Save"
   - Name it: "Vulnerability Monitoring Dashboard"

## 🎯 METHOD 5: Search and Filter

### Use Search Bar:
- **Search by severity:** `severity:critical`
- **Search by type:** `test_type:nmap_scan`
- **Search by target:** `target_ip:192.168.1.*`
- **Search by status:** `workflow_status:IMMORTAL`
- **Search by text:** `"LEGENDARY WORKFLOW"`

### Apply Filters:
1. **Add Filter:**
   - Click "+ Add filter" below search bar
   - Field: `severity`
   - Operator: `is`
   - Value: `critical`

2. **Time Range Filter:**
   - Use time picker to focus on specific periods
   - "Today", "Last 7 days", "Last 30 days"
   - Custom range: Select specific dates

## 🔍 Your Current Data Overview

### What You'll See (9 Total Records):

1. **[15:34:46] SUCCESS** - SYSTEM_STATUS_REPORT
   - Your achievement record with deployment status

2. **[15:20:56] CRITICAL** - legendary_scan  
   - LEGENDARY WORKFLOW VICTORY record

3. **[15:10:00] SUCCESS** - BATTLE_TESTED_WORKFLOW
   - Production readiness confirmation

4. **[15:06:13] INFO** - workflow_demo
   - Workflow demonstration success

5. **[15:04:15] HIGH** - nmap_scan
   - Critical vulnerability discovery

6. **[15:01:09] MEDIUM** - nmap_scan
   - Network scan with 5 open ports

7. **[14:58:33] INFO** - azure_api_test
   - API connection verification

8. **[14:55:14] INFO** - azure_connection_success
   - Connection establishment

9. **[14:48:03] INFO** - azure_connection_test
   - Initial connection test

## 🚀 Pro Tips for Viewing Changes

### 1. **Bookmark Useful Views:**
- Save searches you use frequently
- Create bookmarks for specific severity levels
- Save time ranges you commonly check

### 2. **Use Table View:**
- Click "View: Table" for spreadsheet-like display
- Easier to scan multiple records quickly
- Good for exporting data

### 3. **Expand Record Details:**
- Click the arrow ► next to any record
- View complete JSON data
- See all fields and values

### 4. **Export Your Data:**
- Use "Share" button to export as CSV
- Generate reports for documentation
- Create backups of scan results

### 5. **Set Up Alerts:**
- Go to "Alerting" (if available)
- Create alerts for new critical vulnerabilities
- Get notified when specific conditions occur

## 🎯 Quick Navigation Shortcuts

- **Home:** Overview and getting started
- **Discover:** Browse all your vulnerability data ← **START HERE**
- **Visualize:** Create charts and graphs
- **Dashboard:** Combine multiple views
- **Dev Tools:** Advanced queries and API access
- **Stack Management:** System configuration

## 🌟 Recommended First Steps

1. **Click "Discover"** in left sidebar
2. **Create index pattern:** `vulnerabilities*` 
3. **Set time range:** "Today" or "Last 24 hours"
4. **Add columns:** severity, test_type, target_ip, result
5. **Enable auto-refresh:** 30-second intervals
6. **Start exploring your 9 vulnerability records!**

Your penetration testing data is ready for comprehensive analysis! 🎯
