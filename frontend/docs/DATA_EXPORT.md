# Data Export Guide

## Overview

utxoIQ allows you to export blockchain insights and data in multiple formats for analysis in external tools like Excel, Python, R, or custom applications. This guide covers export formats, usage, and best practices.

## Supported Export Formats

### CSV (Comma-Separated Values)
- **Best for**: Excel, Google Sheets, data analysis tools
- **File extension**: `.csv`
- **Encoding**: UTF-8
- **Delimiter**: Comma (,)
- **Text qualifier**: Double quotes (")

### JSON (JavaScript Object Notation)
- **Best for**: Programming, APIs, data processing
- **File extension**: `.json`
- **Format**: Pretty-printed with 2-space indentation
- **Encoding**: UTF-8
- **Structure**: Array of objects

## Exporting Data

### From Insights Page

#### Export Current View
1. Navigate to **Insights** page
2. Apply desired filters
3. Click **"Export"** button in header
4. Select format (CSV or JSON)
5. File downloads automatically

#### Export Selected Insights
1. Select insights using checkboxes
2. Click **"Export Selected"** button
3. Choose format
4. File downloads with selected data only

### From Insight Detail Page

Export single insight with full details:
1. Open insight detail page
2. Click **"Export"** button
3. Choose format
4. File includes complete insight data and evidence

### From Dashboard Widgets

Export widget data:
1. Click widget menu (⋯)
2. Select **"Export Data"**
3. Choose format
4. Widget data exports to file

## Export Limits

### Free Tier
- **Maximum rows per export**: 100
- **Daily export limit**: 10 exports
- **Formats**: CSV only
- **Batch export**: Not available

### Pro Tier
- **Maximum rows per export**: 1,000
- **Daily export limit**: 50 exports
- **Formats**: CSV and JSON
- **Batch export**: Available

### Power Tier
- **Maximum rows per export**: 10,000
- **Daily export limit**: Unlimited
- **Formats**: CSV, JSON, and API access
- **Batch export**: Available
- **Scheduled exports**: Available

## CSV Export Format

### Structure

```csv
id,category,headline,summary,confidence,createdAt,blockHeight,txCount,evidenceBlocks,evidenceTxids
insight-001,mempool,"High Fee Environment","Mempool congestion...",0.87,2025-11-12T10:30:00Z,870000,1500,"869999,870000","abc123...,def456..."
insight-002,exchange,"Large Exchange Inflow","Significant BTC...",0.92,2025-11-12T09:15:00Z,869998,1,"869998","ghi789..."
```

### Column Definitions

| Column | Type | Description |
|--------|------|-------------|
| `id` | String | Unique insight identifier |
| `category` | String | Category (mempool, exchange, miner, whale) |
| `headline` | String | Insight title |
| `summary` | String | Detailed description |
| `confidence` | Number | Confidence score (0-1) |
| `createdAt` | ISO 8601 | Timestamp of insight generation |
| `blockHeight` | Number | Related block height |
| `txCount` | Number | Number of related transactions |
| `evidenceBlocks` | String | Comma-separated block heights |
| `evidenceTxids` | String | Comma-separated transaction IDs |

### Special Characters

CSV exports handle special characters properly:
- **Commas**: Enclosed in quotes
- **Quotes**: Escaped with double quotes
- **Newlines**: Preserved within quoted fields
- **Unicode**: UTF-8 encoding

### Example Usage

#### Excel
1. Open Excel
2. File → Open
3. Select CSV file
4. Data imports automatically

#### Google Sheets
1. File → Import
2. Upload CSV file
3. Choose import settings
4. Data appears in sheet

#### Python (pandas)
```python
import pandas as pd

# Read CSV
df = pd.read_csv('insights_export.csv')

# Analyze data
high_confidence = df[df['confidence'] > 0.85]
print(high_confidence.describe())
```

## JSON Export Format

### Structure

```json
[
  {
    "id": "insight-001",
    "category": "mempool",
    "headline": "High Fee Environment",
    "summary": "Mempool congestion has increased significantly...",
    "confidence": 0.87,
    "createdAt": "2025-11-12T10:30:00Z",
    "blockHeight": 870000,
    "txCount": 1500,
    "evidence": {
      "blocks": [869999, 870000],
      "txids": ["abc123...", "def456..."]
    },
    "metadata": {
      "source": "utxoiq-insight-generator",
      "version": "1.0",
      "model": "gemini-pro"
    }
  },
  {
    "id": "insight-002",
    "category": "exchange",
    "headline": "Large Exchange Inflow",
    "summary": "Significant BTC moved to exchange wallets...",
    "confidence": 0.92,
    "createdAt": "2025-11-12T09:15:00Z",
    "blockHeight": 869998,
    "txCount": 1,
    "evidence": {
      "blocks": [869998],
      "txids": ["ghi789..."]
    },
    "metadata": {
      "source": "utxoiq-insight-generator",
      "version": "1.0",
      "model": "gemini-pro"
    }
  }
]
```

### Field Definitions

| Field | Type | Description |
|-------|------|-------------|
| `id` | string | Unique insight identifier |
| `category` | string | Insight category |
| `headline` | string | Insight title |
| `summary` | string | Detailed description |
| `confidence` | number | Confidence score (0-1) |
| `createdAt` | string | ISO 8601 timestamp |
| `blockHeight` | number | Related block height |
| `txCount` | number | Transaction count |
| `evidence` | object | Blockchain evidence |
| `evidence.blocks` | number[] | Block heights |
| `evidence.txids` | string[] | Transaction IDs |
| `metadata` | object | Generation metadata |

### Example Usage

#### Python
```python
import json

# Read JSON
with open('insights_export.json', 'r') as f:
    insights = json.load(f)

# Filter high confidence
high_conf = [i for i in insights if i['confidence'] > 0.85]

# Group by category
from collections import defaultdict
by_category = defaultdict(list)
for insight in insights:
    by_category[insight['category']].append(insight)
```

#### JavaScript/Node.js
```javascript
const fs = require('fs');

// Read JSON
const insights = JSON.parse(
  fs.readFileSync('insights_export.json', 'utf8')
);

// Analyze
const avgConfidence = insights.reduce(
  (sum, i) => sum + i.confidence, 0
) / insights.length;

console.log(`Average confidence: ${avgConfidence}`);
```

#### R
```r
library(jsonlite)

# Read JSON
insights <- fromJSON('insights_export.json')

# Convert to data frame
df <- as.data.frame(insights)

# Analyze
summary(df$confidence)
```

## Filename Conventions

### Automatic Naming

Exported files use descriptive names:

```
insights_[filters]_[timestamp].csv
insights_[filters]_[timestamp].json
```

Examples:
- `insights_mempool_high-confidence_2025-11-12_103045.csv`
- `insights_whale_last-24h_2025-11-12_103045.json`
- `insights_all_2025-11-12_103045.csv`

### Custom Naming

Specify custom filename:
1. Click **"Export Options"** before exporting
2. Enter custom filename
3. File extension added automatically

## Advanced Export Options

### Filter Criteria in Filename

Export filenames include active filters:
- **Search terms**: Sanitized and truncated
- **Categories**: Abbreviated (mem, exch, min, wha)
- **Confidence**: Threshold value
- **Date range**: Start and end dates

### Column Selection (Pro/Power)

Choose which columns to export:
1. Click **"Export Options"**
2. Select **"Choose Columns"**
3. Check/uncheck columns
4. Click **"Export"**

### Date Format Options

Customize date formatting:
- **ISO 8601** (default): `2025-11-12T10:30:00Z`
- **Unix timestamp**: `1731408600`
- **Human readable**: `Nov 12, 2025 10:30 AM`

## Batch Export (Pro/Power)

### Export Multiple Filters

Export data for multiple filter combinations:
1. Create filter presets
2. Click **"Batch Export"**
3. Select presets to export
4. Choose format
5. Files download as ZIP archive

### Scheduled Exports (Power)

Automate regular exports:
1. Navigate to **Settings → Exports**
2. Click **"Create Scheduled Export"**
3. Configure:
   - Frequency (daily, weekly, monthly)
   - Time of day
   - Filters to apply
   - Format (CSV or JSON)
   - Delivery method (download, email, webhook)
4. Save schedule

## API Export

### Direct API Access (Power)

Export via API for automation:

```bash
# Export insights as JSON
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://api.utxoiq.com/v1/insights/export?format=json&category=mempool&minConfidence=0.85" \
  -o insights.json

# Export as CSV
curl -H "Authorization: Bearer YOUR_API_KEY" \
  "https://api.utxoiq.com/v1/insights/export?format=csv&dateRange=last-24h" \
  -o insights.csv
```

### API Parameters

| Parameter | Type | Description |
|-----------|------|-------------|
| `format` | string | Export format (csv, json) |
| `category` | string | Filter by category |
| `minConfidence` | number | Minimum confidence (0-1) |
| `dateRange` | string | Time range filter |
| `limit` | number | Maximum rows |
| `offset` | number | Pagination offset |

## Best Practices

### Performance

✅ **Do**:
- Export during off-peak hours for large datasets
- Use filters to reduce export size
- Download to local storage first
- Use batch export for multiple filters
- Schedule regular exports instead of manual

❌ **Don't**:
- Export entire database without filters
- Request exports larger than tier limit
- Export same data repeatedly
- Ignore export size warnings
- Export without testing filters first

### Data Quality

✅ **Do**:
- Verify filters before exporting
- Check sample data in preview
- Validate exported data
- Document export parameters
- Keep export logs

❌ **Don't**:
- Export without reviewing filters
- Assume all data is included
- Skip data validation
- Forget export context
- Lose track of export versions

### Security

✅ **Do**:
- Store exports securely
- Use encrypted storage
- Delete old exports
- Limit export sharing
- Track export access

❌ **Don't**:
- Share exports publicly
- Store in unsecured locations
- Keep unnecessary exports
- Share API keys
- Ignore data privacy

## Troubleshooting

### Export Fails

**Problem**: Export doesn't start or fails

**Solutions**:
1. Check internet connection
2. Verify tier limits
3. Reduce export size
4. Try different format
5. Clear browser cache

### Incomplete Data

**Problem**: Export missing expected data

**Solutions**:
1. Verify filter settings
2. Check date range
3. Review tier limits
4. Try smaller export
5. Contact support

### File Won't Open

**Problem**: Exported file won't open in application

**Solutions**:
1. Verify file extension
2. Check file encoding (UTF-8)
3. Try different application
4. Re-export file
5. Check for corruption

### Slow Export

**Problem**: Export takes too long

**Solutions**:
1. Reduce export size
2. Use more specific filters
3. Export during off-peak hours
4. Try CSV instead of JSON
5. Use API for large exports

## Examples

### Excel Analysis

```
1. Export insights as CSV
2. Open in Excel
3. Create pivot table:
   - Rows: Category
   - Values: Count of ID, Average of Confidence
4. Add charts for visualization
5. Filter by date range
```

### Python Analysis

```python
import pandas as pd
import matplotlib.pyplot as plt

# Load data
df = pd.read_csv('insights_export.csv')

# Convert timestamp
df['createdAt'] = pd.to_datetime(df['createdAt'])

# Group by category
category_counts = df['category'].value_counts()

# Plot
category_counts.plot(kind='bar')
plt.title('Insights by Category')
plt.xlabel('Category')
plt.ylabel('Count')
plt.show()

# Confidence analysis
print(f"Average confidence: {df['confidence'].mean():.2f}")
print(f"High confidence (>0.85): {(df['confidence'] > 0.85).sum()}")
```

### R Analysis

```r
library(tidyverse)

# Load data
insights <- read_csv('insights_export.csv')

# Summary statistics
insights %>%
  group_by(category) %>%
  summarise(
    count = n(),
    avg_confidence = mean(confidence),
    high_conf = sum(confidence > 0.85)
  )

# Visualization
ggplot(insights, aes(x = category, y = confidence)) +
  geom_boxplot() +
  theme_minimal() +
  labs(title = "Confidence by Category")
```

## Resources

- [API Documentation](/docs/api/export)
- [Data Schema Reference](/docs/schema)
- [Analysis Examples](/examples/analysis)
- [Video Tutorial](/tutorials/data-export)

## Support

Questions about data export?

- **Documentation**: [docs.utxoiq.com](https://docs.utxoiq.com)
- **API Reference**: [api.utxoiq.com](https://api.utxoiq.com)
- **Support**: support@utxoiq.com

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0
