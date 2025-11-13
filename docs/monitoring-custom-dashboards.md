# Custom Dashboard Creation Guide

## Overview

Custom dashboards allow you to create personalized monitoring views tailored to your specific needs. Build dashboards with drag-and-drop widgets, configure data sources, and share with your team.

## Dashboard Basics

### Dashboard Components

- **Widgets**: Individual visualization components (charts, gauges, stats)
- **Layout**: Grid-based positioning and sizing of widgets
- **Data Sources**: Metrics and queries that power widgets
- **Time Range**: Global or per-widget time selection
- **Refresh Rate**: Automatic data refresh interval

### Widget Types

| Widget Type | Description | Best For |
|------------|-------------|----------|
| Line Chart | Time-series line graph | Trends over time |
| Bar Chart | Vertical or horizontal bars | Comparisons |
| Gauge | Circular progress indicator | Current status |
| Stat Card | Single numeric value | Key metrics |
| Table | Tabular data display | Detailed data |
| Heatmap | Color-coded matrix | Pattern detection |

## Creating Dashboards

### Via Web UI

#### 1. Create New Dashboard

1. Navigate to **Monitoring** → **Dashboards**
2. Click **Create Dashboard**
3. Enter dashboard details:
   - **Name**: Descriptive dashboard name
   - **Description**: Optional description
   - **Tags**: Categorization tags
   - **Visibility**: Private or shared
4. Click **Create**

#### 2. Add Widgets

1. Click **Add Widget** button
2. Select widget type from library
3. Configure widget:
   - **Title**: Widget display name
   - **Data Source**: Select metric or query
   - **Time Range**: Use global or custom range
   - **Display Options**: Colors, labels, formatting
4. Position and resize widget on grid
5. Click **Save Widget**

#### 3. Arrange Layout

- **Drag widgets**: Click and drag to reposition
- **Resize widgets**: Drag corners to resize
- **Snap to grid**: Widgets automatically align to 12-column grid
- **Mobile responsive**: Layout adapts automatically

#### 4. Save Dashboard

Click **Save Dashboard** to persist changes.

### Via API

#### Create Dashboard

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/dashboards \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "API Performance Dashboard",
    "description": "Monitor API response times and error rates",
    "tags": ["api", "performance"],
    "is_public": false,
    "layout": {
      "columns": 12,
      "row_height": 60
    },
    "widgets": [
      {
        "type": "line_chart",
        "title": "API Response Time",
        "position": {"x": 0, "y": 0, "w": 6, "h": 4},
        "data_source": {
          "metric_type": "custom.googleapis.com/web-api/response_time",
          "aggregation": "ALIGN_MEAN",
          "time_range": "1h"
        },
        "display_options": {
          "show_legend": true,
          "y_axis_label": "Milliseconds",
          "color": "#FF5A21"
        }
      },
      {
        "type": "stat_card",
        "title": "Current Error Rate",
        "position": {"x": 6, "y": 0, "w": 3, "h": 2},
        "data_source": {
          "metric_type": "custom.googleapis.com/web-api/error_rate",
          "aggregation": "ALIGN_MEAN",
          "time_range": "5m"
        },
        "display_options": {
          "unit": "%",
          "decimal_places": 2,
          "color_thresholds": [
            {"value": 0, "color": "#16A34A"},
            {"value": 1, "color": "#D97706"},
            {"value": 5, "color": "#DC2626"}
          ]
        }
      }
    ]
  }'
```

#### Response

```json
{
  "id": "dashboard-123",
  "name": "API Performance Dashboard",
  "description": "Monitor API response times and error rates",
  "created_at": "2025-11-11T10:30:00Z",
  "updated_at": "2025-11-11T10:30:00Z",
  "share_token": null,
  "is_public": false
}
```

## Widget Configuration

### Line Chart

```json
{
  "type": "line_chart",
  "title": "CPU Usage Over Time",
  "data_source": {
    "metric_type": "custom.googleapis.com/feature-engine/cpu_usage",
    "aggregation": "ALIGN_MEAN",
    "time_range": "24h",
    "interval_seconds": 300
  },
  "display_options": {
    "show_legend": true,
    "show_points": false,
    "line_width": 2,
    "y_axis_label": "Percentage",
    "y_axis_min": 0,
    "y_axis_max": 100,
    "color": "#FF5A21",
    "fill_opacity": 0.1
  }
}
```

### Bar Chart

```json
{
  "type": "bar_chart",
  "title": "Requests by Service",
  "data_source": {
    "metric_type": "custom.googleapis.com/*/request_count",
    "aggregation": "ALIGN_SUM",
    "time_range": "1h",
    "group_by": ["service_name"]
  },
  "display_options": {
    "orientation": "vertical",
    "show_values": true,
    "color_scheme": "category",
    "x_axis_label": "Service",
    "y_axis_label": "Requests"
  }
}
```

### Gauge

```json
{
  "type": "gauge",
  "title": "Memory Usage",
  "data_source": {
    "metric_type": "custom.googleapis.com/web-api/memory_usage",
    "aggregation": "ALIGN_MEAN",
    "time_range": "5m"
  },
  "display_options": {
    "min": 0,
    "max": 100,
    "unit": "%",
    "color_ranges": [
      {"from": 0, "to": 70, "color": "#16A34A"},
      {"from": 70, "to": 85, "color": "#D97706"},
      {"from": 85, "to": 100, "color": "#DC2626"}
    ],
    "show_value": true,
    "show_min_max": true
  }
}
```

### Stat Card

```json
{
  "type": "stat_card",
  "title": "Active Users",
  "data_source": {
    "metric_type": "custom.googleapis.com/web-api/active_users",
    "aggregation": "ALIGN_MAX",
    "time_range": "5m"
  },
  "display_options": {
    "unit": "",
    "decimal_places": 0,
    "show_trend": true,
    "trend_comparison": "previous_period",
    "font_size": "large",
    "color": "#FF5A21"
  }
}
```

### Table

```json
{
  "type": "table",
  "title": "Top Endpoints by Latency",
  "data_source": {
    "query": "SELECT endpoint, AVG(latency) as avg_latency FROM metrics WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) GROUP BY endpoint ORDER BY avg_latency DESC LIMIT 10"
  },
  "display_options": {
    "columns": [
      {"field": "endpoint", "header": "Endpoint", "width": "60%"},
      {"field": "avg_latency", "header": "Avg Latency", "width": "40%", "format": "duration"}
    ],
    "sortable": true,
    "pagination": false
  }
}
```

### Heatmap

```json
{
  "type": "heatmap",
  "title": "Request Volume by Hour",
  "data_source": {
    "metric_type": "custom.googleapis.com/web-api/request_count",
    "aggregation": "ALIGN_SUM",
    "time_range": "7d",
    "interval_seconds": 3600,
    "group_by": ["hour_of_day", "day_of_week"]
  },
  "display_options": {
    "color_scheme": "sequential",
    "color_range": ["#F4F4F5", "#FF5A21"],
    "show_values": true,
    "x_axis_label": "Hour of Day",
    "y_axis_label": "Day of Week"
  }
}
```

## Data Sources

### Metric Types

Reference any Cloud Monitoring metric:

```
custom.googleapis.com/{service}/{metric}
```

**Examples**:
- `custom.googleapis.com/web-api/response_time`
- `custom.googleapis.com/feature-engine/cpu_usage`
- `custom.googleapis.com/data-ingestion/mempool_size`

### Aggregation Methods

- `ALIGN_MEAN` - Average value
- `ALIGN_SUM` - Sum of values
- `ALIGN_MIN` - Minimum value
- `ALIGN_MAX` - Maximum value
- `ALIGN_COUNT` - Count of data points
- `ALIGN_RATE` - Rate of change
- `ALIGN_PERCENTILE_95` - 95th percentile
- `ALIGN_PERCENTILE_99` - 99th percentile

### Time Ranges

**Predefined**:
- `5m`, `15m`, `30m` - Minutes
- `1h`, `4h`, `12h`, `24h` - Hours
- `7d`, `30d` - Days

**Custom**:
```json
{
  "time_range": "custom",
  "start_time": "2025-11-10T00:00:00Z",
  "end_time": "2025-11-11T00:00:00Z"
}
```

### Custom Queries

Use BigQuery SQL for complex queries:

```json
{
  "data_source": {
    "type": "bigquery",
    "query": "SELECT service_name, AVG(response_time) as avg_response, COUNT(*) as request_count FROM `utxoiq.intel.metrics` WHERE timestamp > TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR) GROUP BY service_name ORDER BY avg_response DESC"
  }
}
```

## Dashboard Management

### List Dashboards

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/dashboards \
  -H "Authorization: Bearer YOUR_API_KEY"
```

**Query Parameters**:
- `tags` - Filter by tags
- `is_public` - Filter by visibility
- `sort` - Sort by name, created_at, updated_at

### Get Dashboard

```bash
curl -X GET https://api.utxoiq.com/api/v1/monitoring/dashboards/{dashboard_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Update Dashboard

```bash
curl -X PATCH https://api.utxoiq.com/api/v1/monitoring/dashboards/{dashboard_id} \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "Updated Dashboard Name",
    "widgets": [...]
  }'
```

### Delete Dashboard

```bash
curl -X DELETE https://api.utxoiq.com/api/v1/monitoring/dashboards/{dashboard_id} \
  -H "Authorization: Bearer YOUR_API_KEY"
```

## Dashboard Sharing

### Generate Share Token

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/dashboards/{dashboard_id}/share \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "is_public": true,
    "expires_at": "2025-12-31T23:59:59Z"
  }'
```

**Response**:
```json
{
  "share_token": "abc123def456",
  "share_url": "https://app.utxoiq.com/dashboards/shared/abc123def456",
  "expires_at": "2025-12-31T23:59:59Z"
}
```

### Access Shared Dashboard

Public dashboards are accessible without authentication:

```
https://app.utxoiq.com/dashboards/shared/{share_token}
```

### Revoke Share Token

```bash
curl -X DELETE https://api.utxoiq.com/api/v1/monitoring/dashboards/{dashboard_id}/share \
  -H "Authorization: Bearer YOUR_API_KEY"
```

### Copy Dashboard

Copy a dashboard to your account:

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/dashboards/{dashboard_id}/copy \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "name": "My Copy of Dashboard"
  }'
```

## Dashboard Templates

### Available Templates

1. **API Performance** - Response times, error rates, throughput
2. **System Resources** - CPU, memory, disk usage
3. **Bitcoin Monitoring** - Mempool, blocks, transactions
4. **User Activity** - Active users, sessions, engagement
5. **Error Tracking** - Error rates, types, affected users

### Create from Template

```bash
curl -X POST https://api.utxoiq.com/api/v1/monitoring/dashboards/from-template \
  -H "Authorization: Bearer YOUR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "template_id": "api-performance",
    "name": "My API Dashboard",
    "service_name": "web-api"
  }'
```

## Advanced Features

### Variables

Define dashboard variables for dynamic filtering:

```json
{
  "variables": [
    {
      "name": "service",
      "type": "query",
      "query": "SELECT DISTINCT service_name FROM metrics",
      "default": "web-api"
    },
    {
      "name": "time_range",
      "type": "constant",
      "options": ["1h", "24h", "7d"],
      "default": "24h"
    }
  ]
}
```

Use variables in widget data sources:

```json
{
  "data_source": {
    "metric_type": "custom.googleapis.com/${service}/response_time",
    "time_range": "${time_range}"
  }
}
```

### Annotations

Add event annotations to charts:

```json
{
  "annotations": [
    {
      "timestamp": "2025-11-11T10:00:00Z",
      "label": "Deployment v2.1.0",
      "color": "#FF5A21"
    }
  ]
}
```

### Alerts on Dashboard

Link alerts to dashboard widgets:

```json
{
  "widget": {
    "type": "line_chart",
    "alerts": [
      {
        "alert_id": "alert-123",
        "show_threshold": true,
        "show_triggers": true
      }
    ]
  }
}
```

## Best Practices

### Dashboard Design

1. **Focus on key metrics**: Don't overcrowd dashboards
2. **Logical grouping**: Group related widgets together
3. **Consistent time ranges**: Use global time range when possible
4. **Color coding**: Use consistent colors for similar metrics
5. **Responsive layout**: Test on different screen sizes

### Performance

1. **Limit widgets**: Maximum 12-15 widgets per dashboard
2. **Optimize queries**: Use appropriate aggregation intervals
3. **Cache data**: Enable caching for frequently accessed data
4. **Lazy loading**: Load widgets as they come into view
5. **Refresh rates**: Use longer intervals for historical data

### Organization

1. **Naming convention**: Use descriptive, consistent names
2. **Tagging**: Tag dashboards for easy discovery
3. **Folders**: Organize dashboards into logical folders
4. **Templates**: Create templates for common patterns
5. **Documentation**: Add descriptions to dashboards and widgets

## Troubleshooting

### Widget Not Loading

1. **Check data source**: Verify metric exists and has data
2. **Review time range**: Ensure time range contains data
3. **Check permissions**: Verify access to metric
4. **Inspect query**: Test query in BigQuery console
5. **Review logs**: Check browser console for errors

### Slow Dashboard

1. **Reduce widgets**: Remove unnecessary widgets
2. **Optimize queries**: Use more efficient aggregations
3. **Increase intervals**: Use longer aggregation intervals
4. **Enable caching**: Cache widget data
5. **Simplify visualizations**: Use simpler chart types

### Sharing Not Working

1. **Check share token**: Verify token is valid and not expired
2. **Review permissions**: Ensure dashboard is marked public
3. **Test URL**: Try accessing in incognito mode
4. **Check expiration**: Verify share hasn't expired
5. **Regenerate token**: Create new share token if needed

## Examples

### API Performance Dashboard

```json
{
  "name": "API Performance",
  "widgets": [
    {
      "type": "stat_card",
      "title": "Avg Response Time",
      "data_source": {
        "metric_type": "custom.googleapis.com/web-api/response_time",
        "aggregation": "ALIGN_MEAN",
        "time_range": "5m"
      }
    },
    {
      "type": "line_chart",
      "title": "Response Time Trend",
      "data_source": {
        "metric_type": "custom.googleapis.com/web-api/response_time",
        "aggregation": "ALIGN_MEAN",
        "time_range": "24h"
      }
    },
    {
      "type": "bar_chart",
      "title": "Requests by Endpoint",
      "data_source": {
        "metric_type": "custom.googleapis.com/web-api/request_count",
        "aggregation": "ALIGN_SUM",
        "time_range": "1h",
        "group_by": ["endpoint"]
      }
    }
  ]
}
```

## API Reference

### Create Dashboard
`POST /api/v1/monitoring/dashboards`

### List Dashboards
`GET /api/v1/monitoring/dashboards`

### Get Dashboard
`GET /api/v1/monitoring/dashboards/{dashboard_id}`

### Update Dashboard
`PATCH /api/v1/monitoring/dashboards/{dashboard_id}`

### Delete Dashboard
`DELETE /api/v1/monitoring/dashboards/{dashboard_id}`

### Share Dashboard
`POST /api/v1/monitoring/dashboards/{dashboard_id}/share`

### Get Widget Data
`POST /api/v1/monitoring/dashboards/{dashboard_id}/widget-data`

For detailed API documentation, see [API Reference](./api-reference-monitoring.md).
