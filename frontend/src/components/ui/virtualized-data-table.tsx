'use client';

import * as React from 'react';
import {
  ColumnDef,
  SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
} from '@tanstack/react-table';
import { useVirtualizer } from '@tanstack/react-virtual';

interface VirtualizedDataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  onSortingChange?: (sorting: SortingState) => void;
  initialSorting?: SortingState;
  estimateSize?: number; // Estimated row height for virtualization
  overscan?: number; // Number of items to render outside visible area
}

export function VirtualizedDataTable<TData, TValue>({
  columns,
  data,
  onSortingChange,
  initialSorting = [],
  estimateSize = 60,
  overscan = 10,
}: VirtualizedDataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>(initialSorting);
  const tableContainerRef = React.useRef<HTMLDivElement>(null);

  // Track performance for sorting operations
  const sortingTimeRef = React.useRef<number>(0);

  const table = useReactTable({
    data,
    columns,
    getCoreRowModel: getCoreRowModel(),
    getSortedRowModel: getSortedRowModel(),
    onSortingChange: (updater) => {
      const startTime = performance.now();
      
      setSorting((old) => {
        const newSorting = typeof updater === 'function' ? updater(old) : updater;
        
        const endTime = performance.now();
        sortingTimeRef.current = endTime - startTime;
        
        // Log warning if sorting takes longer than 200ms (requirement)
        if (sortingTimeRef.current > 200) {
          console.warn(
            `Sorting took ${sortingTimeRef.current.toFixed(2)}ms (exceeds 200ms requirement for ${data.length} rows)`
          );
        }
        
        // Notify parent component of sorting change
        onSortingChange?.(newSorting);
        
        return newSorting;
      });
    },
    state: {
      sorting,
    },
    enableMultiSort: true,
  });

  const { rows } = table.getRowModel();

  // Virtualization setup
  const rowVirtualizer = useVirtualizer({
    count: rows.length,
    getScrollElement: () => tableContainerRef.current,
    estimateSize: () => estimateSize,
    overscan,
  });

  const virtualRows = rowVirtualizer.getVirtualItems();
  const totalSize = rowVirtualizer.getTotalSize();

  const paddingTop = virtualRows.length > 0 ? virtualRows[0]?.start || 0 : 0;
  const paddingBottom =
    virtualRows.length > 0
      ? totalSize - (virtualRows[virtualRows.length - 1]?.end || 0)
      : 0;

  return (
    <div className="rounded-md border border-border">
      <div
        ref={tableContainerRef}
        className="overflow-auto"
        style={{ maxHeight: '600px' }}
      >
        <table className="w-full">
          <thead className="sticky top-0 z-10 bg-surface border-b border-border">
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id}>
                {headerGroup.headers.map((header) => (
                  <th
                    key={header.id}
                    className="px-4 py-3 text-left text-sm font-medium text-text-primary"
                  >
                    {header.isPlaceholder
                      ? null
                      : flexRender(
                          header.column.columnDef.header,
                          header.getContext()
                        )}
                  </th>
                ))}
              </tr>
            ))}
          </thead>
          <tbody>
            {paddingTop > 0 && (
              <tr>
                <td style={{ height: `${paddingTop}px` }} />
              </tr>
            )}
            {virtualRows.map((virtualRow) => {
              const row = rows[virtualRow.index];
              return (
                <tr
                  key={row.id}
                  className="border-b border-border hover:bg-surface/50 transition-colors"
                  style={{
                    height: `${virtualRow.size}px`,
                  }}
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-sm text-text-primary">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              );
            })}
            {paddingBottom > 0 && (
              <tr>
                <td style={{ height: `${paddingBottom}px` }} />
              </tr>
            )}
            {rows.length === 0 && (
              <tr>
                <td
                  colSpan={columns.length}
                  className="px-4 py-8 text-center text-sm text-muted-foreground"
                >
                  No results.
                </td>
              </tr>
            )}
          </tbody>
        </table>
      </div>
      <div className="px-4 py-2 text-xs text-muted-foreground border-t border-border">
        Showing {virtualRows.length} of {rows.length} rows
      </div>
    </div>
  );
}
