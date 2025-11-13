'use client';

import { useState, useRef, useCallback } from 'react';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';
import { WidgetRenderer } from './widget-renderer';
import { DashboardWidget } from '@/types';
import { GripVertical, Maximize2, X } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface SortableWidgetProps {
  widget: DashboardWidget;
  onResize?: (widgetId: string, newSize: { w: number; h: number }) => void;
  onRemove?: (widgetId: string) => void;
}

export function SortableWidget({ widget, onResize, onRemove }: SortableWidgetProps) {
  const {
    attributes,
    listeners,
    setNodeRef,
    transform,
    transition,
    isDragging,
  } = useSortable({
    id: widget.id,
  });

  const [isResizing, setIsResizing] = useState(false);
  const [resizeStart, setResizeStart] = useState({ x: 0, y: 0, w: 0, h: 0 });
  const widgetRef = useRef<HTMLDivElement>(null);

  const handleResizeStart = useCallback(
    (e: React.MouseEvent) => {
      e.preventDefault();
      e.stopPropagation();
      setIsResizing(true);
      setResizeStart({
        x: e.clientX,
        y: e.clientY,
        w: widget.position.w,
        h: widget.position.h,
      });
    },
    [widget.position]
  );

  const handleResizeMove = useCallback(
    (e: MouseEvent) => {
      if (!isResizing || !widgetRef.current) return;

      const deltaX = e.clientX - resizeStart.x;
      const deltaY = e.clientY - resizeStart.y;

      // Calculate new size based on grid (each grid unit is approximately 1/12 of container width)
      // Assuming each grid column is roughly 100px, adjust based on your layout
      const gridUnitWidth = 100; // Approximate width of one grid column
      const gridUnitHeight = 100; // Approximate height of one grid row

      const newW = Math.max(
        1,
        Math.min(12, resizeStart.w + Math.round(deltaX / gridUnitWidth))
      );
      const newH = Math.max(
        1,
        Math.min(6, resizeStart.h + Math.round(deltaY / gridUnitHeight))
      );

      // Only update if size changed
      if (newW !== widget.position.w || newH !== widget.position.h) {
        onResize?.(widget.id, { w: newW, h: newH });
      }
    },
    [isResizing, resizeStart, widget.id, widget.position, onResize]
  );

  const handleResizeEnd = useCallback(() => {
    setIsResizing(false);
  }, []);

  // Add event listeners for resize
  useState(() => {
    if (isResizing) {
      window.addEventListener('mousemove', handleResizeMove);
      window.addEventListener('mouseup', handleResizeEnd);
      return () => {
        window.removeEventListener('mousemove', handleResizeMove);
        window.removeEventListener('mouseup', handleResizeEnd);
      };
    }
  });

  const style = {
    transform: CSS.Transform.toString(transform),
    transition: isResizing ? 'none' : transition,
    opacity: isDragging ? 0.5 : 1,
  };

  return (
    <div
      ref={(node) => {
        setNodeRef(node);
        if (node) {
          (widgetRef as any).current = node;
        }
      }}
      style={style}
      className="relative group md:col-span-auto"
      // Use inline styles for grid positioning on desktop only
      {...(typeof window !== 'undefined' && window.innerWidth >= 768 ? {
        style: {
          ...style,
          gridColumn: `span ${widget.position.w}`,
          gridRow: `span ${widget.position.h}`,
        }
      } : {})}
    >
      {/* Control buttons */}
      <div className="absolute top-2 right-2 z-10 flex gap-1 opacity-0 group-hover:opacity-100 transition-opacity">
        {/* Remove button */}
        {onRemove && (
          <Button
            variant="ghost"
            size="sm"
            className="h-6 w-6 p-0 bg-surface/80 backdrop-blur-sm hover:bg-destructive hover:text-destructive-foreground"
            onClick={(e) => {
              e.stopPropagation();
              onRemove(widget.id);
            }}
            aria-label="Remove widget"
          >
            <X className="h-3 w-3" />
          </Button>
        )}

        {/* Drag handle */}
        <div
          {...attributes}
          {...listeners}
          className="cursor-grab active:cursor-grabbing p-1 rounded bg-surface/80 backdrop-blur-sm"
          aria-label="Drag to reposition widget"
        >
          <GripVertical className="h-4 w-4 text-text-secondary" />
        </div>
      </div>

      {/* Resize handle */}
      {onResize && (
        <div
          onMouseDown={handleResizeStart}
          className="absolute bottom-0 right-0 z-10 cursor-nwse-resize opacity-0 group-hover:opacity-100 transition-opacity p-2"
          aria-label="Resize widget"
        >
          <Maximize2 className="h-4 w-4 text-text-secondary rotate-90" />
        </div>
      )}

      <WidgetRenderer widget={widget} />
    </div>
  );
}
