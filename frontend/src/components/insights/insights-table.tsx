'use client';

import { useMemo } from 'react';
import { ColumnDef, SortingState } from '@tanstack/react-table';
import { DataTable, DataTableColumnHeader } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Insight, SignalType } from '@/types';
import { format } from 'date-fns';
import Link from 'next/link';
import { BookmarkButton } from './bookmark-button';

interface InsightsTableProps {
  insights: Insight[];
  onSortingChange?: (sorting: SortingState) => void;
  initialSorting?: SortingState;
}

// Category color mapping
const categoryColors: Record<SignalType, string> = {
  mempool: 'bg-orange-500/10 text-orange-500 border-orange-500/20',
  exchange: 'bg-sky-500/10 text-sky-500 border-sky-500/20',
  miner: 'bg-emerald-500/10 text-emerald-500 border-emerald-500/20',
  whale: 'bg-violet-500/10 text-violet-500 border-violet-500/20',
};

// Confidence badge styling
function getConfidenceBadgeVariant(confidence: number): string {
  if (confidence >= 0.85) return 'bg-success/10 text-success border-success/20';
  if (confidence >= 0.7) return 'bg-warning/10 text-warning border-warning/20';
  return 'bg-muted text-muted-foreground border-border';
}

export function InsightsTable({
  insights,
  onSortingChange,
  initialSorting,
}: InsightsTableProps) {
  const columns = useMemo<ColumnDef<Insight>[]>(
    () => [
      {
        accessorKey: 'timestamp',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Time" />
        ),
        cell: ({ row }) => {
          const timestamp = new Date(row.getValue('timestamp'));
          return (
            <div className="flex flex-col">
              <span className="font-medium">
                {format(timestamp, 'MMM d, yyyy')}
              </span>
              <span className="text-xs text-muted-foreground">
                {format(timestamp, 'HH:mm:ss')}
              </span>
            </div>
          );
        },
        sortingFn: 'datetime',
      },
      {
        accessorKey: 'signal_type',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Category" />
        ),
        cell: ({ row }) => {
          const category = row.getValue('signal_type') as SignalType;
          return (
            <Badge
              variant="outline"
              className={`${categoryColors[category]} capitalize`}
            >
              {category}
            </Badge>
          );
        },
      },
      {
        accessorKey: 'headline',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Headline" />
        ),
        cell: ({ row }) => {
          const insight = row.original;
          return (
            <Link
              href={`/insight/${insight.id}`}
              className="hover:underline font-medium max-w-md block truncate"
            >
              {insight.headline}
            </Link>
          );
        },
      },
      {
        accessorKey: 'confidence',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Confidence" />
        ),
        cell: ({ row }) => {
          const confidence = row.getValue('confidence') as number;
          const percentage = Math.round(confidence * 100);
          return (
            <Badge
              variant="outline"
              className={getConfidenceBadgeVariant(confidence)}
            >
              {percentage}%
            </Badge>
          );
        },
        sortingFn: 'basic',
      },
      {
        accessorKey: 'block_height',
        header: ({ column }) => (
          <DataTableColumnHeader column={column} title="Block" />
        ),
        cell: ({ row }) => {
          const blockHeight = row.getValue('block_height') as number | undefined;
          return blockHeight ? (
            <span className="font-mono text-sm">{blockHeight.toLocaleString()}</span>
          ) : (
            <span className="text-muted-foreground">—</span>
          );
        },
        sortingFn: 'basic',
      },
      {
        id: 'actions',
        header: () => <div className="text-right">Actions</div>,
        cell: ({ row }) => {
          const insight = row.original;
          return (
            <div className="flex justify-end">
              <BookmarkButton insightId={insight.id} />
            </div>
          );
        },
      },
    ],
    []
  );

  return (
    <DataTable
      columns={columns}
      data={insights}
      onSortingChange={onSortingChange}
      initialSorting={initialSorting}
    />
  );
}
