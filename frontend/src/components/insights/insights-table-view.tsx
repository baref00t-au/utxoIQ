'use client';

import { useState, useMemo } from 'react';
import { SortingState } from '@tanstack/react-table';
import { InsightsTable } from './insights-table';
import { VirtualizedDataTable } from '@/components/ui/virtualized-data-table';
import { DataTableColumnHeader } from '@/components/ui/data-table';
import { Badge } from '@/components/ui/badge';
import { Button } from '@/components/ui/button';
import { Insight, SignalType, FilterState } from '@/types';
import { format } from 'date-fns';
import Link from 'next/link';
import { BookmarkButton } from './bookmark-button';
import { LayoutGrid, Table } from 'lucide-react';

interface InsightsTableViewProps {
  insights: Insight[];
  filters: FilterState;
  useVirtualization?: boolean;
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

export function InsightsTableView({
  insights,
  filters,
  useVirtualization = false,
}: InsightsTableViewProps) {
  const [sorting, setSorting] = useState<SortingState>([
    { id: 'timestamp', desc: true }, // Default sort by timestamp descending
  ]);

  // Apply filters to insights
  const filteredInsights = useMemo(() => {
    return insights.filter((insight) => {
      // Category filter
      if (filters.categories.length > 0 && 
          !filters.categories.includes(insight.signal_type)) {
        return false;
      }

      // Confidence filter
      if (insight.confidence < filters.minConfidence) {
        return false;
      }

      // Search filter
      if (filters.search) {
        const searchLower = filters.search.toLowerCase();
        const matchesHeadline = insight.headline.toLowerCase().includes(searchLower);
        const matchesSummary = insight.summary.toLowerCase().includes(searchLower);
        if (!matchesHeadline && !matchesSummary) {
          return false;
        }
      }

      // Date range filter
      if (filters.dateRange) {
        const insightDate = new Date(insight.timestamp);
        if (insightDate < filters.dateRange.start || 
            insightDate > filters.dateRange.end) {
          return false;
        }
      }

      return true;
    });
  }, [insights, filters]);

  // Handle sorting change and maintain sort state when filtering
  const handleSortingChange = (newSorting: SortingState) => {
    setSorting(newSorting);
  };

  // Column definitions for virtualized table
  const columns = useMemo(
    () => [
      {
        accessorKey: 'timestamp',
        header: ({ column }: any) => (
          <DataTableColumnHeader column={column} title="Time" />
        ),
        cell: ({ row }: any) => {
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
        header: ({ column }: any) => (
          <DataTableColumnHeader column={column} title="Category" />
        ),
        cell: ({ row }: any) => {
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
        header: ({ column }: any) => (
          <DataTableColumnHeader column={column} title="Headline" />
        ),
        cell: ({ row }: any) => {
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
        header: ({ column }: any) => (
          <DataTableColumnHeader column={column} title="Confidence" />
        ),
        cell: ({ row }: any) => {
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
        header: ({ column }: any) => (
          <DataTableColumnHeader column={column} title="Block" />
        ),
        cell: ({ row }: any) => {
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
        cell: ({ row }: any) => {
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

  // Automatically use virtualization for large datasets (>1000 rows)
  const shouldVirtualize = useVirtualization || filteredInsights.length > 1000;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div className="text-sm text-muted-foreground">
          {filteredInsights.length} {filteredInsights.length === 1 ? 'insight' : 'insights'}
          {shouldVirtualize && ' (virtualized for performance)'}
        </div>
      </div>

      {shouldVirtualize ? (
        <VirtualizedDataTable
          columns={columns}
          data={filteredInsights}
          onSortingChange={handleSortingChange}
          initialSorting={sorting}
          estimateSize={60}
          overscan={10}
        />
      ) : (
        <InsightsTable
          insights={filteredInsights}
          onSortingChange={handleSortingChange}
          initialSorting={sorting}
        />
      )}
    </div>
  );
}
