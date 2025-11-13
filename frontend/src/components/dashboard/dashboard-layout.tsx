'use client';

import { useState, useCallback } from 'react';
import {
  DndContext,
  DragEndEvent,
  DragStartEvent,
  DragOverlay,
  closestCenter,
  PointerSensor,
  useSensor,
  useSensors,
  DragOverEvent,
} from '@dnd-kit/core';
import {
  SortableContext,
  rectSortingStrategy,
  arrayMove,
} from '@dnd-kit/sortable';
import { SortableWidget } from './sortable-widget';
import { WidgetRenderer } from './widget-renderer';
import { WidgetLibrary } from './widget-library';
import { DashboardWidget } from '@/types';

interface DashboardLayoutProps {
  widgets: DashboardWidget[];
  onLayoutChange: (widgets: DashboardWidget[]) => void;
  onAddWidget?: (widget: Omit<DashboardWidget, 'id'>) => void;
  onRemoveWidget?: (widgetId: string) => void;
  editable?: boolean;
  showControls?: boolean;
}

export function DashboardLayout({
  widgets,
  onLayoutChange,
  onAddWidget,
  onRemoveWidget,
  editable = true,
  showControls = true,
}: DashboardLayoutProps) {
  const [activeId, setActiveId] = useState<string | null>(null);

  // Configure sensors for drag detection
  const sensors = useSensors(
    useSensor(PointerSensor, {
      activationConstraint: {
        distance: 8, // 8px movement required to start drag
      },
    })
  );

  const handleDragStart = useCallback((event: DragStartEvent) => {
    setActiveId(event.active.id as string);
  }, []);

  const handleDragEnd = useCallback(
    (event: DragEndEvent) => {
      const { active, over } = event;

      if (over && active.id !== over.id) {
        const oldIndex = widgets.findIndex((w) => w.id === active.id);
        const newIndex = widgets.findIndex((w) => w.id === over.id);

        if (oldIndex !== -1 && newIndex !== -1) {
          const newWidgets = arrayMove(widgets, oldIndex, newIndex);
          onLayoutChange(newWidgets);
        }
      }

      setActiveId(null);
    },
    [widgets, onLayoutChange]
  );

  const handleDragCancel = useCallback(() => {
    setActiveId(null);
  }, []);

  const handleResize = useCallback(
    (widgetId: string, newSize: { w: number; h: number }) => {
      const updatedWidgets = widgets.map((widget) =>
        widget.id === widgetId
          ? {
              ...widget,
              position: { ...widget.position, ...newSize },
            }
          : widget
      );
      onLayoutChange(updatedWidgets);
    },
    [widgets, onLayoutChange]
  );

  const activeWidget = activeId
    ? widgets.find((w) => w.id === activeId)
    : null;

  if (!editable) {
    // Non-editable mode: just render widgets without drag-and-drop
    return (
      <div className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-min">
        {widgets.map((widget) => (
          <div
            key={widget.id}
            className="md:col-span-auto"
            style={{
              gridColumn: `md:span ${widget.position.w}`,
              gridRow: `md:span ${widget.position.h}`,
            }}
          >
            <WidgetRenderer widget={widget} />
          </div>
        ))}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {showControls && editable && onAddWidget && (
        <div className="flex justify-end">
          <WidgetLibrary onAddWidget={onAddWidget} />
        </div>
      )}

      <DndContext
        sensors={sensors}
        collisionDetection={closestCenter}
        onDragStart={handleDragStart}
        onDragEnd={handleDragEnd}
        onDragCancel={handleDragCancel}
      >
        <SortableContext
          items={widgets.map((w) => w.id)}
          strategy={rectSortingStrategy}
        >
          <div className="grid grid-cols-1 md:grid-cols-12 gap-4 auto-rows-min">
            {widgets.map((widget) => (
              <SortableWidget
                key={widget.id}
                widget={widget}
                onResize={handleResize}
                onRemove={onRemoveWidget}
              />
            ))}
          </div>
        </SortableContext>

        <DragOverlay>
          {activeWidget ? (
            <div
              style={{
                gridColumn: `span ${activeWidget.position.w}`,
                gridRow: `span ${activeWidget.position.h}`,
              }}
              className="opacity-50"
            >
              <WidgetRenderer widget={activeWidget} />
            </div>
          ) : null}
        </DragOverlay>
      </DndContext>
    </div>
  );
}
