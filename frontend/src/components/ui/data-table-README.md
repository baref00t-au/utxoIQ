# Data Table Components

This directory contains reusable data table components built with TanStack Table v8.

## Components

### DataTable

A basic sortable data table component with support for single and multi-column sorting.

**Features:**
- Single-column sorting (click column header)
- Multi-column sorting (shift+click column headers)
- Sort indicators with arrows
- Performance monitoring (logs warning if sorting takes >200ms)
- Accessible keyboard navigation
- Responsive design

**Usage:**
```tsx
import { DataTable, DataTableColumnHeader } from '@/components/ui/data-table';
import { ColumnDef } from '@tanstack/react-table';

const columns: ColumnDef<YourDataType>[] = [
  {
    accessorKey: 'name',
    header: ({ column }) => (
      <DataTableColumnHeader column={column} title="Name" />
    ),
  },
  // ... more columns
];

<DataTable
  columns={columns}
  data={data}
  onSortingChange={(sorting) => console.log('Sorting changed:', sorting)}
  initialSorting={[{ id: 'name', desc: false }]}
/>
```

### VirtualizedDataTable

An optimized data table for large datasets (>1000 rows) using virtualization.

**Features:**
- All features from DataTable
- Row virtualization for performance
- Sticky header
- Configurable row height estimation
- Overscan for smooth scrolling
- Automatic performance optimization

**Usage:**
```tsx
import { VirtualizedDataTable } from '@/components/ui/virtualized-data-table';

<VirtualizedDataTable
  columns={columns}
  data={largeDataset}
  estimateSize={60} // Estimated row height in pixels
  overscan={10} // Number of rows to render outside viewport
/>
```

### DataTableColumnHeader

A helper component for creating sortable column headers with visual indicators.

**Features:**
- Sort direction arrows (up/down/both)
- Multi-sort index display
- Accessible button with ARIA labels
- Keyboard support

**Usage:**
```tsx
{
  accessorKey: 'timestamp',
  header: ({ column }) => (
    <DataTableColumnHeader column={column} title="Time" />
  ),
}
```

## Performance Requirements

Per Requirement 11:
- **Sorting speed**: Must sort within 200ms for up to 10,000 rows
- **Multi-column sorting**: Supported via shift+click
- **Sort state persistence**: Maintained when filtering data
- **Visual indicators**: Clear arrows showing sort direction

## Sorting Behavior

### Single-Column Sort
1. Click column header to sort ascending
2. Click again to sort descending
3. Click again to remove sort

### Multi-Column Sort
1. Click first column header to sort
2. Hold Shift and click second column header
3. Continue holding Shift to add more sort columns
4. Sort priority is shown with numbers (1, 2, 3...)

## Accessibility

- All interactive elements are keyboard accessible
- ARIA labels on sort buttons
- Focus indicators visible
- Screen reader announcements for sort changes

## Styling

Tables use CSS variables for theming:
- `--background`: Table background
- `--surface`: Header and hover background
- `--border`: Border color
- `--text-primary`: Primary text color
- `--muted-foreground`: Secondary text color

## Examples

See `frontend/src/components/insights/insights-table.tsx` for a complete implementation example with:
- Custom column definitions
- Badge components for categories
- Confidence score styling
- Timestamp formatting
- Action buttons

## Testing

Run tests with:
```bash
npm test -- data-table
```

Tests cover:
- Single-column sorting
- Multi-column sorting
- Sort performance with large datasets
- Sort state persistence during filtering
- Keyboard navigation
- Accessibility compliance
