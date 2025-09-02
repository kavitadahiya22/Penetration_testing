# 🔍 Azure OpenSearch Dashboard Navigation Guide

## 🌐 Dashboard URL
https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/app/home#/

## 📊 How to View All Your Records

### Method 1: Using Discover Tab
1. **Click on "Discover"** in the left sidebar
2. **Select Index Pattern**: Choose `vulnerabilities*` or create an index pattern
3. **Time Range**: Adjust the time picker (top-right) to show "Last 24 hours" or "Today"
4. **View Records**: All your 9 vulnerability records will be displayed in chronological order

### Method 2: Using Dev Tools
1. **Click on "Dev Tools"** in the left sidebar
2. **Use Query Console**: 
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
3. **Click the Play Button** (▶) to execute the query

### Method 3: Direct API Queries
```powershell
# Get all records
Invoke-RestMethod -Uri "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/vulnerabilities/_search?size=20&sort=@timestamp:desc" -Method GET

# Search specific records
Invoke-RestMethod -Uri "https://cybrty-dev-ca.wonderfuldune-e921120d.eastus.azurecontainerapps.io/es/vulnerabilities/_search?q=legendary" -Method GET
```

## 🎯 Your Current Data Summary (9 Records)

### Records by Type:
- **SYSTEM_STATUS_REPORT**: 1 record (Latest Achievement)
- **legendary_scan**: 1 record (Legendary Victory)
- **BATTLE_TESTED_WORKFLOW**: 1 record (Production Ready)
- **nmap_scan**: 2 records (Network scans)
- **azure_connection_test**: 1 record (Connection validation)
- **azure_connection_success**: 1 record (Connection success)
- **azure_api_test**: 1 record (API functionality)
- **workflow_demo**: 1 record (Demo successful)

### Records by Severity:
- **SUCCESS**: 1 record
- **critical**: 1 record  
- **high**: 1 record
- **medium**: 1 record
- **info**: 4 records
- **success**: 1 record

## 🛠️ Dashboard Features to Explore

### 1. **Visualizations**
- Create charts and graphs from your vulnerability data
- Build dashboards with multiple visualizations
- Monitor trends over time

### 2. **Index Management**
- View index statistics
- Manage index policies
- Configure index templates

### 3. **Search & Filter**
- Use the search bar for specific queries
- Apply filters by severity, test_type, target_ip
- Save searches for future use

### 4. **Export Data**
- Export search results to CSV
- Share visualizations
- Create reports

## 🚀 Quick Navigation Tips

1. **Home Tab**: Overview and getting started
2. **Discover Tab**: Browse and search your data
3. **Visualize Tab**: Create charts and graphs
4. **Dashboard Tab**: Combine multiple visualizations
5. **Dev Tools**: Direct API interaction
6. **Management**: Index and cluster management

## 🎯 Recommended First Steps

1. **Go to Discover Tab**
2. **Create Index Pattern**: `vulnerabilities*`
3. **Set Time Range**: "Last 24 hours"
4. **Explore Your 9 Records**
5. **Try filtering by severity or test_type**

Your penetration testing data is ready for analysis! 🌟
