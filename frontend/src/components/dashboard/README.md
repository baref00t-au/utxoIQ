# Customizable Dashboard Components

This directory contains the implementation of a drag-and-drop customizable dashboard system for utxoIQ.

## Features

- **Drag-and-Drop**: Reposition widgets by dragging them
- **Resizable Widgets**: Resize widgets using corner handles
- **Widget Library**: Add new widgets from a template library
- **Auto-Save**: Layout changes are automatically saved after 2 seconds
- **Grid-Based Layout**: 12-column responsive grid system
- **Multiple Widget Types**: Line charts, bar charts, gauges, and stat cards

## Components

### DashboardLayout

Main container component that handles drag-and-drop functionality.

```tsx
import { DashboardLayout } from '@/components/dashboard';

<DashboardLayout
  widgets={widgets}
  onLayoutChange={handleLayoutChange}
  onAddWidget={handleAddWidget}
  onRemoveWidget={handleRemoveWidget}
  editable={true}
  showControls={true}
/>
```

**Props:**
- `widgets`: Array of DashboardWidget objects
- `onLayoutChange`: Callback when widget positions change
- `onAddWidget`: Callback when a new widget is added
- `onRemoveWidget`: Callback when a widget is removed
- `editable`: Enable/disable editing mode (default: true)
- `showControls`: Show/hide control buttons (default: true)

### CustomizableDashboard

High-level component with built-in persistence.

```tsx
import { CustomizableDashboard } from '@/components/dashboard';

<CustomizableDashboard
  dashboardId="my-dashboard"
  userId="user-123"
  editable={true}
/>
```

**Props:**
- `dashboardId`: Unique identifier for the dashboard
- `userId`: User ID for personalized dashboards
- `editable`: Enable/disable editing mode

### WidgetLibrary

Modal dialog for adding new widgets.

```tsx
import { WidgetLibrary } from '@/components/dashboard';

<WidgetLibrary onAddWidget={handleAddWidget} />
```

### WidgetRenderer

Renders different widget types based on configuration.

**Supported Widget Types:**
- `line_chart`: Time-series line chart
- `bar_chart`: Bar chart for categorical data
- `gauge`: Circular gauge for percentage values
- `stat_card`: Single metric with trend indicator

## Hooks

### useDashboardPersistence

Hook for managing dashboard state with auto-save.

```tsx
import { useDashboardPersistence } from '@/hooks/use-dashboard-persistence';

const {
  widgets,
  isLoading,
  isSaving,
  error,
  addWidget,
  removeWidget,
  updateWidgets,
  saveDashboard,
} = useDashboardPersistence({
  dashboardId: 'my-dashboard',
  userId: 'user-123',
  enabled: true,
});
```

**Features:**
- Automatic loading from backend on mount
- Debounced auto-save (2 seconds after changes)
- Optimistic updates for instant feedback
- Error handling and loading states

## Widget Configuration

Widgets are configured using the `DashboardWidget` type:

```typescript
interface DashboardWidget {
  id: string;
  type: 'line_chart' | 'bar_chart' | 'gauge' | 'stat_card';
  title: string;
  data_source: {
    metric_type: string;
    aggregation: string;
    time_range: string;
  };
  display_options: Record<string, any>;
  position: {
    x: number;
    y: number;
    w: number; // Width in grid columns (1-12)
    h: number; // Height in grid rows
  };
}
```

## Grid System

The dashboard uses a 12-column grid system:
- Widgets can span 1-12 columns in width
- Widgets can span 1-6 rows in height
- Grid snapping ensures consistent alignment
- Responsive breakpoints adjust layout on mobile

## API Integration

The dashboard expects the following backend endpoints:

### GET /api/v1/dashboards/:dashboardId
Load dashboard configuration

**Response:**
```json
{
  "id": "dashboard-1",
  "name": "My Dashboard",
  "widgets": [...],
  "is_public": false,
  "created_at": "2024-01-01T00:00:00Z",
  "updated_at": "2024-01-01T00:00:00Z"
}
```

### PUT /api/v1/dashboards/:dashboardId
Save dashboard configuration

**Request:**
```json
{
  "widgets": [...]
}
```

## Testing

Tests are located in `__tests__` directories:

```bash
# Run all dashboard tests
npm test -- dashboard

# Run specific test file
npm test -- dashboard-layout.test
npm test -- widget-library.test
npm test -- use-dashboard-persistence.test
```

## Accessibility

- All interactive elements are keyboard accessible
- ARIA labels on drag handles and buttons
- Focus indicators visible on all controls
- Screen reader compatible

## Performance

- Lazy loading of widget content
- Debounced auto-save to reduce API calls
- Optimistic updates for instant feedback
- Virtualization support for large dashboards (future enhancement)

## Future Enhancements

- [ ] Widget configuration editor
- [ ] Dashboard templates
- [ ] Export/import dashboard layouts
- [ ] Shared dashboards with permissions
- [ ] Real-time collaboration
- [ ] Custom widget types via plugins
