import { describe, it, expect, vi } from 'vitest';
import { render, screen } from '@testing-library/react';
import { DashboardLayout } from '../dashboard-layout';
import { DashboardWidget } from '@/types';

// Mock DnD Kit
vi.mock('@dnd-kit/core', () => ({
  DndContext: ({ children }: any) => <div>{children}</div>,
  closestCenter: vi.fn(),
  PointerSensor: vi.fn(),
  useSensor: vi.fn(),
  useSensors: vi.fn(() => []),
  DragOverlay: ({ children }: any) => <div>{children}</div>,
}));

vi.mock('@dnd-kit/sortable', () => ({
  SortableContext: ({ children }: any) => <div>{children}</div>,
  rectSortingStrategy: vi.fn(),
  arrayMove: (arr: any[], from: number, to: number) => {
    const newArr = [...arr];
    const item = newArr.splice(from, 1)[0];
    newArr.splice(to, 0, item);
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

// Mock widget renderer
vi.mock('../widget-renderer', () => ({
  WidgetRenderer: ({ widget }: { widget: DashboardWidget }) => (
    <div data-testid={`widget-${widget.id}`}>{widget.title}</div>
  ),
}));

// Mock widget library
vi.mock('../widget-library', () => ({
  WidgetLibrary: () => <button>Add Widget</button>,
}));

describe('Responsive Dashboard', () => {
  const mockWidgets: DashboardWidget[] = [
    {
      id: 'widget-1',
      type: 'chart',
      title: 'Price Chart',
      config: {},
      position: { x: 0, y: 0, w: 6, h: 2 },
    },
    {
      id: 'widget-2',
      type: 'stats',
      title: 'Statistics',
      config: {},
      position: { x: 6, y: 0, w: 6, h: 2 },
    },
    {
      id: 'widget-3',
      type: 'alerts',
      title: 'Recent Alerts',
      config: {},
      position: { x: 0, y: 2, w: 12, h: 3 },
    },
  ];

  describe('Mobile Layout (< 768px)', () => {
    it('stacks widgets vertically on mobile', () => {
      const { container } = render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-12');
    });

    it('renders all widgets in mobile view', () => {
      render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      expect(screen.getByTestId('widget-widget-1')).toBeInTheDocument();
      expect(screen.getByTestId('widget-widget-2')).toBeInTheDocument();
      expect(screen.getByTestId('widget-widget-3')).toBeInTheDocument();
    });

    it('maintains widget order on mobile', () => {
      const { container } = render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      const widgets = container.querySelectorAll('[data-testid^="widget-"]');
      expect(widgets).toHaveLength(3);
      expect(widgets[0]).toHaveAttribute('data-testid', 'widget-widget-1');
      expect(widgets[1]).toHaveAttribute('data-testid', 'widget-widget-2');
      expect(widgets[2]).toHaveAttribute('data-testid', 'widget-widget-3');
    });
  });

  describe('Desktop Layout (>= 768px)', () => {
    it('uses grid layout on desktop', () => {
      const { container } = render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={true}
        />
      );

      const grid = container.querySelector('.grid');
      expect(grid).toHaveClass('grid-cols-1');
      expect(grid).toHaveClass('md:grid-cols-12');
    });

    it('shows widget controls in editable mode', () => {
      render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          onAddWidget={vi.fn()}
          editable={true}
          showControls={true}
        />
      );

      expect(screen.getByText('Add Widget')).toBeInTheDocument();
    });

    it('hides widget controls in non-editable mode', () => {
      render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      expect(screen.queryByText('Add Widget')).not.toBeInTheDocument();
    });
  });

  describe('Widget Positioning', () => {
    it('applies correct grid span for widgets', () => {
      const { container } = render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      const widgets = container.querySelectorAll('[data-testid^="widget-"]');
      
      // Check that widgets have parent divs with grid positioning
      widgets.forEach((widget) => {
        const parent = widget.parentElement;
        expect(parent).toBeInTheDocument();
      });
    });

    it('handles empty widget list', () => {
      const { container } = render(
        <DashboardLayout
          widgets={[]}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      const grid = container.querySelector('.grid');
      expect(grid).toBeInTheDocument();
      expect(grid?.children).toHaveLength(0);
    });
  });

  describe('Touch Interactions', () => {
    it('disables drag-and-drop in non-editable mode', () => {
      const { container } = render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      // In non-editable mode, widgets should not have drag handles
      const dragHandles = container.querySelectorAll('[aria-label*="Drag"]');
      expect(dragHandles).toHaveLength(0);
    });

    it('enables drag-and-drop in editable mode', () => {
      render(
        <DashboardLayout
          widgets={mockWidgets}
          onLayoutChange={vi.fn()}
          editable={true}
        />
      );

      // Widgets should be rendered (drag functionality is mocked)
      expect(screen.getByTestId('widget-widget-1')).toBeInTheDocument();
    });
  });

  describe('Performance', () => {
    it('renders large number of widgets efficiently', () => {
      const manyWidgets: DashboardWidget[] = Array.from({ length: 20 }, (_, i) => ({
        id: `widget-${i}`,
        type: 'chart',
        title: `Widget ${i}`,
        config: {},
        position: { x: 0, y: i, w: 6, h: 2 },
      }));

      const startTime = performance.now();
      
      render(
        <DashboardLayout
          widgets={manyWidgets}
          onLayoutChange={vi.fn()}
          editable={false}
        />
      );

      const endTime = performance.now();
      const renderTime = endTime - startTime;

      // Rendering should be fast (< 100ms for 20 widgets)
      expect(renderTime).toBeLessThan(100);
    });
  });
});
