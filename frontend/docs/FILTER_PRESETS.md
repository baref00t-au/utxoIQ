# Filter Presets Guide

## Overview

Filter presets allow you to save and quickly apply your most-used filter combinations. Instead of manually configuring filters each time, save your common searches as presets and apply them with a single click.

## What Are Filter Presets?

Filter presets are saved combinations of:
- **Search terms**: Full-text search queries
- **Category filters**: Mempool, Exchange, Miner, Whale
- **Confidence thresholds**: Minimum confidence scores
- **Date ranges**: Time period filters
- **Sort options**: Sorting preferences

## Creating Filter Presets

### Step 1: Configure Filters

Set up your desired filters in the Insights page:

1. Navigate to the **Insights** page
2. Configure filters in the left sidebar:
   - Enter search terms
   - Select categories
   - Adjust confidence slider
   - Set date range
3. Verify results match your expectations

### Step 2: Save as Preset

1. Click **"Save Filters"** button above filter panel
2. Enter a descriptive name (e.g., "High Confidence Mempool")
3. Optionally add a description
4. Click **"Save Preset"**
5. Preset appears in your saved presets list

### Quick Save

Use keyboard shortcut:
- **Ctrl/Cmd + Shift + S**: Quick save current filters

## Using Filter Presets

### Applying Presets

#### From Sidebar
1. Open **"Saved Presets"** section in filter panel
2. Click preset name to apply
3. Filters update immediately
4. Results refresh automatically

#### From Dropdown
1. Click **"Presets"** dropdown in header
2. Select preset from list
3. Filters apply instantly

#### Keyboard Shortcut
- **Ctrl/Cmd + 1-9**: Apply preset 1-9
- **?**: Show all keyboard shortcuts

### Preset Indicators

When a preset is active:
- Preset name appears in filter header
- Active indicator (•) next to preset name
- "Clear Preset" button available

## Managing Presets

### Editing Presets

1. Hover over preset in list
2. Click **"Edit"** icon (✏️)
3. Modify preset settings:
   - Change name
   - Update description
   - Adjust filters
4. Click **"Save Changes"**

### Deleting Presets

1. Hover over preset in list
2. Click **"Delete"** icon (🗑️)
3. Confirm deletion
4. Preset removed permanently

### Reordering Presets

Drag and drop to reorder:
1. Click and hold preset drag handle (⋮⋮)
2. Drag to new position
3. Release to drop
4. Order saves automatically

### Duplicating Presets

Create variations of existing presets:
1. Hover over preset
2. Click **"Duplicate"** icon (📋)
3. Preset copied with "(Copy)" suffix
4. Edit duplicate as needed

## Preset Limits

### Free Tier
- **Maximum presets**: 3
- **Shared presets**: Not available
- **Export/Import**: Not available

### Pro Tier
- **Maximum presets**: 10
- **Shared presets**: Not available
- **Export/Import**: Available

### Power Tier
- **Maximum presets**: Unlimited
- **Shared presets**: Available
- **Export/Import**: Available
- **Team presets**: Available

## Advanced Features

### Preset Descriptions

Add detailed descriptions to presets:
```
Name: High Value Whale Movements
Description: Tracks whale transactions over 100 BTC with high confidence scores, focusing on exchange deposits that might indicate selling pressure.
```

### Preset Tags

Organize presets with tags:
- **Trading**: Presets for trading decisions
- **Research**: Presets for analysis
- **Monitoring**: Presets for ongoing surveillance
- **Alerts**: Presets for alert configuration

### Default Preset

Set a preset as default:
1. Right-click preset
2. Select **"Set as Default"**
3. Preset applies automatically on page load

### Preset Sharing (Power Tier)

Share presets with team members:
1. Click **"Share"** icon on preset
2. Choose sharing method:
   - Copy link
   - Email invite
   - Team workspace
3. Recipients can import preset

## Common Preset Examples

### High Confidence Insights
```
Search: (empty)
Categories: All
Confidence: ≥ 85%
Date Range: Last 24 hours
Sort: Newest first
```

### Mempool Congestion Alerts
```
Search: "fee" OR "congestion" OR "mempool"
Categories: Mempool
Confidence: ≥ 70%
Date Range: Last 4 hours
Sort: Confidence (high to low)
```

### Exchange Deposit Monitoring
```
Search: "deposit" OR "inflow"
Categories: Exchange
Confidence: ≥ 75%
Date Range: Last 24 hours
Sort: Newest first
```

### Whale Activity Tracking
```
Search: (empty)
Categories: Whale
Confidence: ≥ 80%
Date Range: Last 7 days
Sort: Newest first
```

### Mining Pool Analysis
```
Search: "pool" OR "hashrate" OR "difficulty"
Categories: Miner
Confidence: ≥ 70%
Date Range: Last 30 days
Sort: Relevance
```

## Preset Best Practices

### Naming Conventions

✅ **Good Names**:
- "High Confidence Mempool Alerts"
- "Whale Movements > 100 BTC"
- "Exchange Outflows (Last 24h)"
- "Mining Pool Hashrate Changes"

❌ **Poor Names**:
- "Preset 1"
- "Test"
- "asdf"
- "My Filters"

### Organization Tips

1. **Use descriptive names**: Clearly indicate what the preset filters for
2. **Add descriptions**: Explain the purpose and use case
3. **Group by purpose**: Trading, research, monitoring, etc.
4. **Regular cleanup**: Delete unused presets
5. **Version presets**: "Whale Tracking v2" for iterations

### Performance Considerations

- **Avoid overly broad searches**: Narrow filters perform better
- **Use confidence thresholds**: Reduce result set size
- **Limit date ranges**: Shorter ranges load faster
- **Test before saving**: Verify preset returns expected results

## Keyboard Shortcuts

### Preset Management
- **Ctrl/Cmd + Shift + S**: Save current filters as preset
- **Ctrl/Cmd + 1-9**: Apply preset 1-9
- **Ctrl/Cmd + Shift + C**: Clear active preset
- **Ctrl/Cmd + Shift + E**: Edit active preset

### Filter Navigation
- **/**: Focus search input
- **Escape**: Clear all filters
- **Tab**: Navigate between filter controls

## Exporting and Importing

### Export Presets (Pro/Power)

Export presets to JSON file:
1. Click **"Preset Options"** menu (⋯)
2. Select **"Export Presets"**
3. Choose presets to export (or all)
4. Save JSON file

### Import Presets (Pro/Power)

Import presets from JSON file:
1. Click **"Preset Options"** menu
2. Select **"Import Presets"**
3. Choose JSON file
4. Review presets to import
5. Click **"Import"**

### Preset JSON Format

```json
{
  "version": "1.0",
  "presets": [
    {
      "id": "preset-1",
      "name": "High Confidence Mempool",
      "description": "Mempool insights with 85%+ confidence",
      "filters": {
        "search": "",
        "categories": ["mempool"],
        "minConfidence": 85,
        "dateRange": {
          "start": "2025-11-11T00:00:00Z",
          "end": "2025-11-12T00:00:00Z"
        }
      },
      "createdAt": "2025-11-12T10:00:00Z",
      "updatedAt": "2025-11-12T10:00:00Z"
    }
  ]
}
```

## API Integration

### Programmatic Preset Management

For advanced users and integrations:

#### List Presets
```typescript
const presets = await fetch('/api/v1/filters/presets')
  .then(r => r.json());
```

#### Create Preset
```typescript
await fetch('/api/v1/filters/presets', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'My Preset',
    filters: {
      search: 'whale',
      categories: ['whale'],
      minConfidence: 80
    }
  })
});
```

#### Update Preset
```typescript
await fetch(`/api/v1/filters/presets/${presetId}`, {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({
    name: 'Updated Name',
    filters: {...}
  })
});
```

#### Delete Preset
```typescript
await fetch(`/api/v1/filters/presets/${presetId}`, {
  method: 'DELETE'
});
```

#### Apply Preset
```typescript
const preset = await fetch(`/api/v1/filters/presets/${presetId}`)
  .then(r => r.json());

// Apply filters from preset
applyFilters(preset.filters);
```

## Troubleshooting

### Preset Not Saving

**Problem**: Preset doesn't appear in list after saving

**Solutions**:
1. Check internet connection
2. Verify you're signed in
3. Check preset limit for your tier
4. Try refreshing the page
5. Check browser console for errors

### Preset Not Applying

**Problem**: Clicking preset doesn't update filters

**Solutions**:
1. Refresh the page
2. Clear browser cache
3. Check if preset was modified
4. Try re-creating the preset
5. Report issue to support

### Missing Presets

**Problem**: Presets disappeared after update

**Solutions**:
1. Check if signed in to correct account
2. Verify presets weren't deleted
3. Check if import/export backup exists
4. Contact support for recovery

### Preset Limit Reached

**Problem**: Can't create more presets

**Solutions**:
1. Delete unused presets
2. Upgrade to higher tier
3. Export presets for backup
4. Consolidate similar presets

## Tips and Tricks

### Quick Preset Creation

1. Start with broad filters
2. Refine until results are relevant
3. Save as preset immediately
4. Iterate and create variations

### Preset Workflows

**Morning Routine**:
1. Apply "Overnight Whale Activity" preset
2. Review high-confidence insights
3. Switch to "Mempool Status" preset
4. Check for congestion alerts

**Trading Session**:
1. Apply "Exchange Flows" preset
2. Monitor large deposits/withdrawals
3. Switch to "Price Action Insights" preset
4. Track market-moving events

**Research Mode**:
1. Apply "Historical Analysis" preset
2. Extend date range as needed
3. Export results for analysis
4. Save new presets for future research

### Preset Combinations

While you can't apply multiple presets simultaneously, you can:
1. Apply base preset
2. Manually adjust additional filters
3. Save as new combined preset

## Resources

- [Filter Documentation](/docs/filters)
- [API Reference](/docs/api/filters)
- [Video Tutorial](/tutorials/filter-presets)
- [Community Presets](/community/presets)

## Support

Questions about filter presets?

- **Documentation**: [docs.utxoiq.com](https://docs.utxoiq.com)
- **Community**: [community.utxoiq.com](https://community.utxoiq.com)
- **Support**: support@utxoiq.com

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0
