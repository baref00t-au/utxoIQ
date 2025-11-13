'use client';

import * as React from 'react';
import {
  ColumnDef,
  SortingState,
  flexRender,
  getCoreRowModel,
  getSortedRowModel,
  useReactTable,
  ColumnSort,
} from '@tanstack/react-table';
import { ArrowUpDown, ArrowUp, ArrowDown } from 'lucide-react';
import { Button } from '@/components/ui/button';

interface DataTableProps<TData, TValue> {
  columns: ColumnDef<TData, TValue>[];
  data: TData[];
  onSortingChange?: (sorting: SortingState) => void;
  initialSorting?: SortingState;
}

export function DataTable<TData, TValue>({
  columns,
  data,
  onSortingChange,
  initialSorting = [],
}: DataTableProps<TData, TValue>) {
  const [sorting, setSorting] = React.useState<SortingState>(initialSorting);

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
    enableMultiSort: true, // Enable multi-column sorting with shift-click
  });

  return (
    <div className="rounded-md border border-border">
      <div className="overflow-x-auto">
        <table className="w-full">
          <thead>
            {table.getHeaderGroups().map((headerGroup) => (
              <tr key={headerGroup.id} className="border-b border-border bg-surface">
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
            {table.getRowModel().rows?.length ? (
              table.getRowModel().rows.map((row) => (
                <tr
                  key={row.id}
                  className="border-b border-border hover:bg-surface/50 transition-colors"
                >
                  {row.getVisibleCells().map((cell) => (
                    <td key={cell.id} className="px-4 py-3 text-sm text-text-primary">
                      {flexRender(cell.column.columnDef.cell, cell.getContext())}
                    </td>
                  ))}
                </tr>
              ))
            ) : (
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
    </div>
  );
}

// Helper component for sortable column headers
interface DataTableColumnHeaderProps<TData, TValue>
  extends React.HTMLAttributes<HTMLDivElement> {
  column: any;
  title: string;
}

export function DataTableColumnHeader<TData, TValue>({
  column,
  title,
  className,
}: DataTableColumnHeaderProps<TData, TValue>) {
  if (!column.getCanSort()) {
    return <div className={className}>{title}</div>;
  }

  const sortDirection = column.getIsSorted();
  const sortIndex = column.getSortIndex();
  const isMultiSort = sortIndex !== -1 && column.getIsSorted();

  return (
    <div className={`flex items-center space-x-2 ${className || ''}`}>
      <Button
        variant="ghost"
        size="sm"
        className="-ml-3 h-8 data-[state=open]:bg-accent"
        onClick={(e) => {
          // Support multi-column sorting with shift-click
          column.toggleSorting(undefined, e.shiftKey);
        }}
        aria-label={`Sort by ${title}`}
      >
        <span>{title}</span>
        {sortDirection === 'asc' ? (
          <ArrowUp className="ml-2 h-4 w-4" aria-hidden="true" />
        ) : sortDirection === 'desc' ? (
          <ArrowDown className="ml-2 h-4 w-4" aria-hidden="true" />
        ) : (
          <ArrowUpDown className="ml-2 h-4 w-4 opacity-50" aria-hidden="true" />
        )}
        {isMultiSort && (
          <span className="ml-1 text-xs text-muted-foreground">
            {sortIndex + 1}
          </span>
        )}
      </Button>
    </div>
  );
}
