# Interactive Charts

Interactive chart components with zoom, pan, and export capabilities.

## Components

### InteractiveChart

A fully-featured interactive chart component built with Recharts that provides zoom, pan, and export functionality.

#### Features

- **Zoom**: Click and drag to select an area to zoom into
- **Pan**: Navigate through zoomed data by selecting new areas
- **Reset**: Button to return to the full data view
- **Tooltips**: Crosshair with value tooltips on hover
- **Export**: PNG (2x resolution) and SVG export with theme colors
- **Theme Support**: Automatically adapts to dark/light theme
- **Accessibility**: ARIA labels and keyboard navigation

#### Usage

```typescript
import { InteractiveChart } from '@/components/charts';

const data = [
  { timestamp: '2024-01-01', value: 100 },
  { timestamp: '2024-01-02', value: 150 },
  { timestamp: '2024-01-03', value: 120 },
  { timestamp: '2024-01-04', value: 180 },
  { timestamp: '2024-01-05', value: 200 },
];

export function MyComponent() {
  return (
    <InteractiveChart
      data={data}
      title="Bitcoin Price"
      dataKey="value"
      xAxisKey="timestamp"
      height={400}
      showGrid={true}
      strokeColor="#FF5A21"
    />
  );
}
```

#### Props

| Prop | Type | Default | Description |
|------|------|---------|-------------|
| `data` | `ChartDataPoint[]` | Required | Array of data points to display |
| `title` | `string` | `'Chart'` | Chart title displayed above the chart |
| `dataKey` | `string` | `'value'` | Key in data objects for Y-axis values |
| `xAxisKey` | `string` | `'timestamp'` | Key in data objects for X-axis values |
| `height` | `number` | `400` | Chart height in pixels |
| `showGrid` | `boolean` | `true` | Whether to show grid lines |
| `strokeColor` | `string` | Theme brand color | Custom line color (overrides theme) |

#### Data Format

```typescript
interface ChartDataPoint {
  timestamp: string | number;
  value: number;
  [key: string]: any; // Additional properties allowed
}
```

#### Examples

##### Basic Usage

```typescript
<InteractiveChart
  data={priceData}
  title="Bitcoin Price (USD)"
/>
```

##### Custom Styling

```typescript
<InteractiveChart
  data={volumeData}
  title="Trading Volume"
  dataKey="volume"
  xAxisKey="date"
  height={300}
  showGrid={false}
  strokeColor="#10B981"
/>
```

##### With Custom Data Keys

```typescript
const customData = [
  { date: '2024-01-01', price: 45000 },
  { date: '2024-01-02', price: 46000 },
];

<InteractiveChart
  data={customData}
  title="Custom Chart"
  dataKey="price"
  xAxisKey="date"
/>
```

#### Interactions

1. **Zoom In**: Click and drag across the chart to select an area. Release to zoom into that area.
2. **Reset Zoom**: Click the "Reset Zoom" button to return to the full data view.
3. **View Tooltips**: Hover over the chart to see a crosshair and value tooltips.
4. **Export PNG**: Click "Export" → "Export as PNG" to download a high-resolution PNG.
5. **Export SVG**: Click "Export" → "Export as SVG" to download a vector graphic.

#### Keyboard Navigation

- `Tab`: Navigate between controls
- `Enter`/`Space`: Activate buttons
- `Escape`: Close export dropdown menu

#### Accessibility

- All buttons have ARIA labels
- Keyboard navigation supported
- Focus indicators visible
- Screen reader compatible

#### Performance

- Handles datasets with 1000+ data points efficiently
- Exports complete within 2 seconds
- Smooth zoom transitions (300ms)
- Optimized rendering with Recharts

#### Theme Integration

The component automatically adapts to the current theme:

**Dark Theme:**
- Background: `#0B0B0C`
- Surface: `#131316`
- Grid: `#2A2A2E`
- Text: `#A1A1AA`
- Stroke: `#FF5A21` (brand color)

**Light Theme:**
- Background: `#FFFFFF`
- Surface: `#F9FAFB`
- Grid: `#E5E7EB`
- Text: `#6B7280`
- Stroke: `#FF5A21` (brand color)

#### Export Filenames

Exported files use the following naming convention:
- Format: `{title-slug}-{date}.{extension}`
- Example: `bitcoin-price-2024-01-15.png`

#### Browser Support

- Chrome/Edge: Full support
- Firefox: Full support
- Safari: Full support
- Mobile browsers: Full support (touch interactions work)

#### Dependencies

- `recharts`: Chart rendering
- `html2canvas`: PNG export
- `lucide-react`: Icons
- Theme context from `@/lib/theme`

#### Testing

Comprehensive test suite with 21 tests covering:
- Rendering
- Zoom functionality
- Pan functionality
- Tooltip display
- Chart export (PNG/SVG)
- Theme support
- Accessibility
- Performance

Run tests:
```bash
npm test -- src/components/charts/__tests__/interactive-chart.test.tsx
```
