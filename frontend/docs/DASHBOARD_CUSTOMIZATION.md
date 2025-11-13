# Dashboard Customization Guide

## Overview

utxoIQ provides a fully customizable dashboard that allows users to arrange, resize, and configure widgets according to their workflow preferences. This guide explains how to use the drag-and-drop dashboard system, manage widgets, and persist your layout.

## Dashboard Features

### Drag-and-Drop Layout
- Reposition widgets by dragging them to new locations
- Grid-based snapping for consistent alignment
- Visual feedback during drag operations
- Automatic layout adjustment

### Widget Resizing
- Resize widgets by dragging corner handles
- Grid-constrained resizing for consistency
- Minimum and maximum size limits
- Responsive sizing on mobile devices

### Widget Library
- Add widgets from a comprehensive library
- Remove widgets you don't need
- Configure widget-specific settings
- Save custom widget configurations

### Layout Persistence
- Layouts automatically save to your account
- Sync across all your devices
- Restore default layout anytime
- Export/import layout configurations

## Using the Dashboard

### Accessing the Dashboard

Navigate to the dashboard page:
```
https://utxoiq.com/dashboard
```

Or click "Dashboard" in the main navigation menu.

### Rearranging Widgets

#### Desktop
1. **Hover** over a widget header
2. **Click and hold** the drag handle (⋮⋮ icon)
3. **Drag** the widget to desired position
4. **Release** to drop in new location

#### Mobile/Tablet
1. **Long press** on widget header (500ms)
2. **Drag** to new position
3. **Release** to drop

### Resizing Widgets

#### Desktop
1. **Hover** over widget corner
2. **Click and drag** resize handle
3. **Release** when desired size is reached

#### Mobile/Tablet
- Widgets automatically stack vertically
- Resizing disabled on small screens
- Full-width layout for optimal viewing

### Adding Widgets

1. Click **"Add Widget"** button (+ icon) in dashboard header
2. Browse available widgets in the widget library
3. Click widget card to preview
4. Click **"Add to Dashboard"** to add widget
5. Widget appears in next available position

### Removing Widgets

1. **Hover** over widget you want to remove
2. Click **"Remove"** button (× icon) in widget header
3. Confirm removal in dialog
4. Widget is removed from dashboard

### Configuring Widgets

1. Click **"Settings"** icon (⚙️) in widget header
2. Modify widget-specific settings:
   - Data source
   - Time range
   - Display options
   - Refresh interval
3. Click **"Save"** to apply changes

## Available Widgets

### Insight Feed Widget
**Description**: Real-time stream of blockchain insights  
**Size**: 1×2 to 4×4 grid units  
**Configuration**:
- Category filter (All, Mempool, Exchange, Miner, Whale)
- Confidence threshold
- Number of insights to display

### Price Chart Widget
**Description**: Bitcoin price chart with technical indicators  
**Size**: 2×2 to 4×3 grid units  
**Configuration**:
- Time range (1h, 4h, 24h, 7d, 30d)
- Chart type (Line, Candlestick, Area)
- Indicators (MA, RSI, MACD)

### Mempool Monitor Widget
**Description**: Real-time mempool statistics  
**Size**: 1×1 to 2×2 grid units  
**Configuration**:
- Metrics to display
- Alert thresholds
- Refresh interval

### Exchange Flow Widget
**Description**: Track Bitcoin flows to/from exchanges  
**Size**: 2×2 to 4×3 grid units  
**Configuration**:
- Exchange selection
- Time range
- Flow direction (Inflow, Outflow, Net)

### Alert Summary Widget
**Description**: Overview of your active alerts  
**Size**: 1×1 to 2×2 grid units  
**Configuration**:
- Alert categories
- Status filter
- Sort order

### Network Stats Widget
**Description**: Bitcoin network statistics  
**Size**: 1×1 to 2×2 grid units  
**Configuration**:
- Metrics selection
- Update frequency

### Whale Activity Widget
**Description**: Large transaction monitoring  
**Size**: 2×2 to 4×3 grid units  
**Configuration**:
- Minimum transaction size
- Time range
- Entity filter

### Mining Stats Widget
**Description**: Mining pool and hashrate data  
**Size**: 2×2 to 3×2 grid units  
**Configuration**:
- Pool selection
- Metrics display
- Time range

## Layout Management

### Saving Layouts

Layouts automatically save when you:
- Move a widget
- Resize a widget
- Add or remove a widget
- Change widget configuration

**Auto-save delay**: 2 seconds after last change

### Manual Save

Force immediate save:
1. Click **"Save Layout"** button in dashboard header
2. Confirmation message appears
3. Layout saved to your account

### Restoring Default Layout

Reset to default configuration:
1. Click **"Layout Options"** menu (⋯)
2. Select **"Restore Default Layout"**
3. Confirm in dialog
4. Dashboard resets to default configuration

### Exporting Layout

Save layout configuration to file:
1. Click **"Layout Options"** menu
2. Select **"Export Layout"**
3. Choose export format (JSON)
4. Save file to your device

### Importing Layout

Load layout from file:
1. Click **"Layout Options"** menu
2. Select **"Import Layout"**
3. Choose JSON file
4. Confirm import
5. Dashboard updates with imported layout

## Grid System

### Grid Specifications

- **Columns**: 12 columns (desktop), 4 columns (tablet), 1 column (mobile)
- **Row height**: 80px
- **Gap**: 16px between widgets
- **Minimum widget size**: 1×1 grid units
- **Maximum widget size**: 4×4 grid units

### Grid Units

Widget sizes are specified in grid units:
- **1×1**: Small widget (e.g., single metric)
- **2×2**: Medium widget (e.g., chart)
- **3×2**: Wide widget (e.g., table)
- **4×3**: Large widget (e.g., detailed chart)

### Responsive Behavior

#### Desktop (≥1024px)
- 12-column grid
- Full drag-and-drop functionality
- All widget sizes available

#### Tablet (640px - 1023px)
- 4-column grid
- Drag-and-drop enabled
- Widgets scale proportionally

#### Mobile (≤639px)
- Single column layout
- Widgets stack vertically
- Drag-and-drop disabled
- Full-width widgets

## Keyboard Shortcuts

### Navigation
- **Tab**: Move focus between widgets
- **Shift + Tab**: Move focus backward
- **Enter**: Open widget settings
- **Escape**: Close widget settings

### Widget Management
- **Ctrl/Cmd + A**: Add new widget
- **Delete**: Remove focused widget
- **Ctrl/Cmd + S**: Save layout
- **Ctrl/Cmd + R**: Restore default layout

### Accessibility
- **Arrow keys**: Navigate within widget
- **Space**: Toggle widget expansion
- **?**: Show keyboard shortcuts help

## Advanced Features

### Widget Grouping

Group related widgets:
1. Select multiple widgets (Ctrl/Cmd + Click)
2. Right-click selection
3. Choose **"Group Widgets"**
4. Grouped widgets move together

### Widget Templates

Save widget configurations as templates:
1. Configure widget settings
2. Click **"Save as Template"**
3. Name your template
4. Template appears in widget library

### Shared Layouts

Share layouts with team members:
1. Export layout to JSON
2. Share file with team
3. Team members import layout
4. Everyone uses same configuration

### Layout Presets

Quick-access layout presets:
- **Trader**: Price charts, order flow, alerts
- **Analyst**: Insights, network stats, whale activity
- **Miner**: Mining stats, mempool, network health
- **Researcher**: All data widgets, detailed views

## Performance Optimization

### Widget Refresh Rates

Configure refresh intervals per widget:
- **Real-time**: Updates every 5 seconds
- **Fast**: Updates every 30 seconds
- **Normal**: Updates every 60 seconds
- **Slow**: Updates every 5 minutes

### Data Caching

- Widget data cached for performance
- Cache duration varies by widget type
- Manual refresh available for all widgets

### Lazy Loading

- Widgets load on-demand
- Off-screen widgets defer loading
- Improves initial page load time

## Troubleshooting

### Layout Not Saving

**Problem**: Changes don't persist after refresh

**Solutions**:
1. Check internet connection
2. Verify you're signed in
3. Check browser console for errors
4. Try manual save
5. Clear browser cache and retry

### Widgets Not Responding

**Problem**: Drag-and-drop not working

**Solutions**:
1. Refresh the page
2. Check browser compatibility
3. Disable browser extensions
4. Try different browser
5. Report issue to support

### Layout Looks Wrong

**Problem**: Widgets overlap or misaligned

**Solutions**:
1. Restore default layout
2. Clear browser cache
3. Check screen resolution
4. Try different zoom level
5. Report layout bug

### Performance Issues

**Problem**: Dashboard feels slow

**Solutions**:
1. Reduce number of widgets
2. Increase refresh intervals
3. Disable animations (Settings)
4. Close unused browser tabs
5. Check system resources

## Best Practices

### Layout Design

✅ **Do**:
- Group related widgets together
- Place frequently used widgets at top
- Use appropriate widget sizes
- Leave some empty space
- Test on different screen sizes

❌ **Don't**:
- Overcrowd the dashboard
- Use too many large widgets
- Hide important information
- Ignore mobile layout
- Forget to save changes

### Widget Configuration

✅ **Do**:
- Set appropriate refresh rates
- Configure relevant filters
- Use descriptive widget titles
- Enable only needed features
- Test widget settings

❌ **Don't**:
- Use real-time refresh for everything
- Display too much data per widget
- Ignore widget performance
- Forget to configure alerts
- Leave default settings unchanged

### Performance

✅ **Do**:
- Limit total number of widgets (8-12 recommended)
- Use appropriate refresh intervals
- Enable data caching
- Monitor browser performance
- Close unused widgets

❌ **Don't**:
- Add every available widget
- Set all widgets to real-time
- Ignore performance warnings
- Keep unused widgets
- Disable caching

## API Integration

### Programmatic Layout Management

For advanced users, manage layouts via API:

```typescript
// Get current layout
const layout = await fetch('/api/v1/dashboard/layout').then(r => r.json());

// Update layout
await fetch('/api/v1/dashboard/layout', {
  method: 'PUT',
  headers: { 'Content-Type': 'application/json' },
  body: JSON.stringify({ widgets: [...] })
});

// Reset to default
await fetch('/api/v1/dashboard/layout/reset', {
  method: 'POST'
});
```

### Widget Data API

Fetch widget data programmatically:

```typescript
// Get widget data
const data = await fetch(`/api/v1/widgets/${widgetId}/data`).then(r => r.json());

// Update widget config
await fetch(`/api/v1/widgets/${widgetId}/config`, {
  method: 'PUT',
  body: JSON.stringify({ config: {...} })
});
```

## Examples

### Creating a Trader Dashboard

1. Add **Price Chart Widget** (4×3) at top
2. Add **Order Flow Widget** (2×2) below
3. Add **Alert Summary Widget** (2×1) on right
4. Add **Mempool Monitor Widget** (2×1) below alerts
5. Configure real-time refresh for price chart
6. Set alert thresholds
7. Save as "Trader" template

### Creating an Analyst Dashboard

1. Add **Insight Feed Widget** (3×4) on left
2. Add **Network Stats Widget** (2×2) top right
3. Add **Whale Activity Widget** (2×2) middle right
4. Add **Exchange Flow Widget** (4×3) at bottom
5. Configure filters for high-confidence insights
6. Set appropriate time ranges
7. Save as "Analyst" template

## Resources

- [Widget Library Documentation](/docs/widgets)
- [API Reference](/docs/api)
- [Video Tutorials](/tutorials/dashboard)
- [Community Layouts](/community/layouts)

## Support

Need help with dashboard customization?

- **Documentation**: [docs.utxoiq.com](https://docs.utxoiq.com)
- **Community**: [community.utxoiq.com](https://community.utxoiq.com)
- **Support**: support@utxoiq.com
- **Discord**: [discord.gg/utxoiq](https://discord.gg/utxoiq)

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0
