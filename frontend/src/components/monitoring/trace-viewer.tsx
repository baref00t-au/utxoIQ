'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Badge } from '@/components/ui/badge';
import { fetchTrace } from '@/lib/api';
import { Trace, TraceSpan } from '@/types';
import { Search, Clock, AlertCircle, CheckCircle, ChevronRight, ChevronDown } from 'lucide-react';
import { format, parseISO } from 'date-fns';

export function TraceViewer() {
  const [traceId, setTraceId] = useState('');
  const [searchedTraceId, setSearchedTraceId] = useState('');
  const [expandedSpans, setExpandedSpans] = useState<Set<string>>(new Set());

  const { data: traceData, isLoading, error } = useQuery({
    queryKey: ['trace', searchedTraceId],
    queryFn: () => fetchTrace(searchedTraceId),
    enabled: !!searchedTraceId,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    if (traceId.trim()) {
      setSearchedTraceId(traceId.trim());
    }
  };

  const toggleSpan = (spanId: string) => {
    const newExpanded = new Set(expandedSpans);
    if (newExpanded.has(spanId)) {
      newExpanded.delete(spanId);
    } else {
      newExpanded.add(spanId);
    }
    setExpandedSpans(newExpanded);
  };

  const buildSpanHierarchy = (spans: TraceSpan[]) => {
    const spanMap = new Map<string, TraceSpan & { children: TraceSpan[] }>();
    const rootSpans: (TraceSpan & { children: TraceSpan[] })[] = [];

    // Create map of all spans
    spans.forEach((span) => {
      spanMap.set(span.span_id, { ...span, children: [] });
    });

    // Build hierarchy
    spans.forEach((span) => {
      const spanWithChildren = spanMap.get(span.span_id)!;
      if (span.parent_span_id) {
        const parent = spanMap.get(span.parent_span_id);
        if (parent) {
          parent.children.push(spanWithChildren);
        } else {
          rootSpans.push(spanWithChildren);
        }
      } else {
        rootSpans.push(spanWithChildren);
      }
    });

    return rootSpans;
  };

  const getSpanColor = (span: TraceSpan) => {
    if (span.status === 'error') return 'bg-destructive';
    if (span.duration_ms > 1000) return 'bg-warning';
    return 'bg-success';
  };

  const calculateSpanPosition = (span: TraceSpan, totalDuration: number) => {
    const startTime = new Date(span.start_time).getTime();
    const traceStartTime = traceData?.spans
      ? Math.min(...traceData.spans.map((s: TraceSpan) => new Date(s.start_time).getTime()))
      : startTime;
    
    const offset = ((startTime - traceStartTime) / totalDuration) * 100;
    const width = (span.duration_ms / totalDuration) * 100;
    
    return { offset, width };
  };

  const renderSpan = (
    span: TraceSpan & { children: TraceSpan[] },
    depth: number = 0,
    totalDuration: number
  ) => {
    const isExpanded = expandedSpans.has(span.span_id);
    const hasChildren = span.children.length > 0;
    const { offset, width } = calculateSpanPosition(span, totalDuration);

    return (
      <div key={span.span_id} className="space-y-1">
        <div
          className="flex items-center gap-2 p-2 hover:bg-muted/50 rounded cursor-pointer"
          style={{ paddingLeft: `${depth * 24 + 8}px` }}
          onClick={() => hasChildren && toggleSpan(span.span_id)}
        >
          <div className="flex-shrink-0 w-4">
            {hasChildren && (
              <Button variant="ghost" size="icon" className="h-4 w-4 p-0">
                {isExpanded ? (
                  <ChevronDown className="h-3 w-3" />
                ) : (
                  <ChevronRight className="h-3 w-3" />
                )}
              </Button>
            )}
          </div>

          <div className="flex-1 min-w-0">
            <div className="flex items-center gap-2 mb-1">
              <span className="text-sm font-medium truncate">{span.name}</span>
              <Badge variant="outline" className={getSpanColor(span)}>
                {span.duration_ms.toFixed(2)}ms
              </Badge>
              {span.status === 'error' && (
                <AlertCircle className="h-4 w-4 text-destructive" />
              )}
              {span.status === 'ok' && span.duration_ms < 100 && (
                <CheckCircle className="h-4 w-4 text-success" />
              )}
            </div>

            {/* Timeline bar */}
            <div className="relative h-6 bg-muted rounded overflow-hidden">
              <div
                className={`absolute h-full ${getSpanColor(span)} opacity-70`}
                style={{
                  left: `${offset}%`,
                  width: `${Math.max(width, 0.5)}%`,
                }}
              />
            </div>

            {isExpanded && span.attributes && (
              <div className="mt-2 p-2 bg-muted/30 rounded text-xs">
                <pre className="font-mono overflow-x-auto">
                  {JSON.stringify(span.attributes, null, 2)}
                </pre>
              </div>
            )}
          </div>

          <div className="flex-shrink-0 text-xs text-muted-foreground">
            {format(parseISO(span.start_time), 'HH:mm:ss.SSS')}
          </div>
        </div>

        {isExpanded &&
          span.children.map((child) => renderSpan(child, depth + 1, totalDuration))}
      </div>
    );
  };

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Trace Search
          </CardTitle>
          <CardDescription>Enter a trace ID to view the distributed trace</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="flex gap-2">
            <div className="flex-1">
              <Label htmlFor="trace-id" className="sr-only">
                Trace ID
              </Label>
              <Input
                id="trace-id"
                value={traceId}
                onChange={(e) => setTraceId(e.target.value)}
                placeholder="Enter trace ID (e.g., 1234567890abcdef)"
                className="font-mono"
              />
            </div>
            <Button type="submit" disabled={isLoading || !traceId.trim()}>
              {isLoading ? 'Loading...' : 'Search'}
            </Button>
          </form>
        </CardContent>
      </Card>

      {/* Trace Details */}
      {error && (
        <Card>
          <CardContent className="py-8">
            <div className="text-center">
              <AlertCircle className="h-12 w-12 text-destructive mx-auto mb-4" />
              <p className="text-muted-foreground">
                Trace not found. Please check the trace ID and try again.
              </p>
            </div>
          </CardContent>
        </Card>
      )}

      {traceData && (
        <>
          {/* Trace Summary */}
          <Card>
            <CardHeader>
              <CardTitle>Trace Summary</CardTitle>
              <CardDescription>Trace ID: {traceData.trace_id}</CardDescription>
            </CardHeader>
            <CardContent>
              <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
                <div>
                  <p className="text-sm text-muted-foreground">Total Duration</p>
                  <p className="text-2xl font-semibold">
                    {traceData.total_duration_ms.toFixed(2)}ms
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Total Spans</p>
                  <p className="text-2xl font-semibold">{traceData.spans.length}</p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Error Spans</p>
                  <p className="text-2xl font-semibold">
                    {traceData.spans.filter((s: TraceSpan) => s.status === 'error').length}
                  </p>
                </div>
                <div>
                  <p className="text-sm text-muted-foreground">Slow Spans (&gt;1s)</p>
                  <p className="text-2xl font-semibold">
                    {traceData.spans.filter((s: TraceSpan) => s.duration_ms > 1000).length}
                  </p>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Trace Timeline */}
          <Card>
            <CardHeader>
              <CardTitle className="flex items-center gap-2">
                <Clock className="h-5 w-5" />
                Trace Timeline
              </CardTitle>
              <CardDescription>
                Hierarchical view of spans with timing information
              </CardDescription>
            </CardHeader>
            <CardContent>
              <div className="space-y-1">
                {buildSpanHierarchy(traceData.spans).map((span) =>
                  renderSpan(span, 0, traceData.total_duration_ms)
                )}
              </div>

              {/* Legend */}
              <div className="mt-6 pt-4 border-t flex items-center gap-6 text-sm">
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-success rounded" />
                  <span>Fast (&lt;100ms)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-warning rounded" />
                  <span>Slow (&gt;1s)</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-4 bg-destructive rounded" />
                  <span>Error</span>
                </div>
              </div>
            </CardContent>
          </Card>

          {/* Slow Spans Highlight */}
          {traceData.spans.filter((s: TraceSpan) => s.duration_ms > 1000).length > 0 && (
            <Card>
              <CardHeader>
                <CardTitle className="flex items-center gap-2">
                  <AlertCircle className="h-5 w-5 text-warning" />
                  Slow Spans
                </CardTitle>
                <CardDescription>Spans taking longer than 1 second</CardDescription>
              </CardHeader>
              <CardContent>
                <div className="space-y-2">
                  {traceData.spans
                    .filter((s: TraceSpan) => s.duration_ms > 1000)
                    .sort((a: TraceSpan, b: TraceSpan) => b.duration_ms - a.duration_ms)
                    .map((span: TraceSpan) => (
                      <div
                        key={span.span_id}
                        className="flex items-center justify-between p-3 border rounded-lg"
                      >
                        <div>
                          <p className="font-medium">{span.name}</p>
                          <p className="text-sm text-muted-foreground">
                            {format(parseISO(span.start_time), 'HH:mm:ss.SSS')}
                          </p>
                        </div>
                        <Badge variant="outline" className="bg-warning">
                          {span.duration_ms.toFixed(2)}ms
                        </Badge>
                      </div>
                    ))}
                </div>
              </CardContent>
            </Card>
          )}
        </>
      )}

      {!searchedTraceId && !error && (
        <Card>
          <CardContent className="py-12">
            <div className="text-center">
              <Search className="h-12 w-12 text-muted-foreground mx-auto mb-4" />
              <p className="text-muted-foreground">
                Enter a trace ID above to view distributed trace details
              </p>
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  );
}
