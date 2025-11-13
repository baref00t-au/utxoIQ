import { describe, it, expect, vi, beforeEach } from 'vitest';
import { render, screen, fireEvent, waitFor } from '@testing-library/react';
import { DashboardLayout } from '../dashboard-layout';
import { DashboardWidget } from '@/types';

// Mock @dnd-kit modules
vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: any) => <div data-testid="dnd-context">{children}</div>,
  DragOverlay: ({ children }: any) => <div data-testid="drag-overlay">{children}</div>,
  closestCenter: vi.fn(),
  PointerSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
}));

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: any) => <div data-testid="sortable-context">{children}</div>,
  rectSortingStrategy: vi.fn(),
  arrayMove: (arr: any[], oldIndex: number, newIndex: number) => {
    const newArr = [...arr];
    const [removed] = newArr.splice(oldIndex, 1);
    newArr.splice(newIndex, 0, removed);
    return newArr;
  },
  useSortable: () => ({
    attributes: {},
    listeners: {},
    setNodeRef: vi.fn(),
    transform: null,
    transition: null,
    isDragging: false,
  }),
}));

vi.mock('@dnd-kit/utilities', () => ({
  CSS: {
    Transform: {
      toString: () => '',
    },
  },
}));

const mockWidgets: DashboardWidget[] = [
  {
    id: 'widget-1',
    type: 'line_chart',
    title: 'CPU Usage',
    data_source: {
      metric_type: 'cpu_usage',
      aggregation: 'avg',
      time_range: '24h',
    },
    display_options: {},
    position: { x: 0, y: 0, w: 6, h: 2 },
  },
  {
    id: 'widget-2',
    type: 'stat_card',
    title: 'Active Users',
    data_source: {
      metric_type: 'active_users',
      aggregation: 'count',
      time_range: '24h',
    },
    display_options: {},
    position: { x: 6, y: 0, w: 3, h: 1 },
  },
];

describe('DashboardLayout', () => {
  let onLayoutChange: ReturnType<typeof vi.fn>;
  let onAddWidget: ReturnType<typeof vi.fn>;
  let onRemoveWidget: ReturnType<typeof vi.fn>;

  beforeEach(() => {
    onLayoutChange = vi.fn();
    onAddWidget = vi.fn();
    onRemoveWidget = vi.fn();
  });

  it('renders widgets in grid layout', () => {
    render(
      <DashboardLayout
        widgets={mockWidgets}
        onLayoutChange={onLayoutChange}
      />
    );

    expect(screen.getByText('CPU Usage')).toBeInTheDocument();
    expect(screen.getByText('Active Users')).toBeInTheDocument();
  });

  it('renders in non-editable mode without drag handles', () => {
    render(
      <DashboardLayout
        widgets={mockWidgets}
        onLayoutChange={onLayoutChange}
        editable={false}
      />
    );

    // Should not render DnD context in non-editable mode
    expect(screen.queryByTestId('dnd-context')).not.toBeInTheDocument();
  });

  it('shows widget library button when editable and showControls is true', () => {
    render(
      <DashboardLayout
        widgets={mockWidgets}
        onLayoutChange={onLayoutChange}
        onAddWidget={onAddWidget}
        editable={true}
        showControls={true}
      />
    );

    expect(screen.getByText('Add Widget')).toBeInTheDocument();
  });

  it('hides widget library button when showControls is false', () => {
    render(
      <DashboardLayout
        widgets={mockWidgets}
        onLayoutChange={onLayoutChange}
        onAddWidget={onAddWidget}
        editable={true}
        showControls={false}
      />
    );

    expect(screen.queryByText('Add Widget')).not.toBeInTheDocument();
  });

  it('renders empty state when no widgets', () => {
    render(
      <DashboardLayout
        widgets={[]}
        onLayoutChange={onLayoutChange}
        editable={true}
      />
    );

    // Grid should still be rendered but empty
    const grid = screen.getByTestId('sortable-context');
    expect(grid).toBeInTheDocument();
  });

  it('applies correct grid column span to widgets', () => {
    const { container } = render(
      <DashboardLayout
        widgets={mockWidgets}
        onLayoutChange={onLayoutChange}
      />
    );

    const widgets = container.querySelectorAll('[style*="grid-column"]');
    expect(widgets.length).toBeGreaterThan(0);
  });
});
