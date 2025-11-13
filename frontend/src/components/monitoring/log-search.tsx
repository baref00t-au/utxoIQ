'use client';

import { useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Input } from '@/components/ui/input';
import { Label } from '@/components/ui/label';
import { Button } from '@/components/ui/button';
import { Select, SelectContent, SelectItem, SelectTrigger, SelectValue } from '@/components/ui/select';
import { Badge } from '@/components/ui/badge';
import { searchLogs, fetchLogContext } from '@/lib/api';
import { LogEntry } from '@/types';
import { Search, Download, ChevronDown, ChevronUp, Loader2 } from 'lucide-react';
import { format, parseISO } from 'date-fns';

const SEVERITY_COLORS = {
  DEBUG: 'bg-gray-500',
  INFO: 'bg-blue-500',
  WARNING: 'bg-yellow-500',
  ERROR: 'bg-red-500',
  CRITICAL: 'bg-red-700',
};

export function LogSearch() {
  const [searchQuery, setSearchQuery] = useState('');
  const [filters, setFilters] = useState({
    service: '',
    severity: '',
    start_time: '',
    end_time: '',
    limit: 100,
  });
  const [expandedLog, setExpandedLog] = useState<string | null>(null);
  const [contextLog, setContextLog] = useState<string | null>(null);

  const { data: logsData, isLoading, refetch } = useQuery({
    queryKey: ['logs', searchQuery, filters],
    queryFn: () => searchLogs(searchQuery, filters),
    enabled: false, // Only fetch when user clicks search
  });

  const { data: contextData, isLoading: contextLoading } = useQuery({
    queryKey: ['log-context', contextLog],
    queryFn: () => fetchLogContext(contextLog!, 10),
    enabled: !!contextLog,
  });

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault();
    refetch();
  };

  const exportToCSV = () => {
    if (!logsData?.logs) return;

    const headers = ['Timestamp', 'Severity', 'Service', 'Message'];
    const rows = logsData.logs.map((log: LogEntry) => [
      log.timestamp,
      log.severity,
      log.service,
      log.message.replace(/"/g, '""'), // Escape quotes
    ]);

    const csv = [
      headers.join(','),
      ...rows.map((row: string[]) => row.map((cell) => `"${cell}"`).join(',')),
    ].join('\n');

    const blob = new Blob([csv], { type: 'text/csv' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = `logs-${new Date().toISOString()}.csv`;
    a.click();
    URL.revokeObjectURL(url);
  };

  const highlightText = (text: string, query: string) => {
    if (!query) return text;
    
    const parts = text.split(new RegExp(`(${query})`, 'gi'));
    return parts.map((part, i) =>
      part.toLowerCase() === query.toLowerCase() ? (
        <mark key={i} className="bg-brand/30 text-foreground">
          {part}
        </mark>
      ) : (
        part
      )
    );
  };

  const logs = logsData?.logs || [];

  return (
    <div className="space-y-6">
      {/* Search Form */}
      <Card>
        <CardHeader>
          <CardTitle className="flex items-center gap-2">
            <Search className="h-5 w-5" />
            Log Search
          </CardTitle>
          <CardDescription>Search and filter logs across all services</CardDescription>
        </CardHeader>
        <CardContent>
          <form onSubmit={handleSearch} className="space-y-4">
            <div>
              <Label htmlFor="search-query">Search Query</Label>
              <Input
                id="search-query"
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                placeholder="Enter search terms..."
              />
            </div>

            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <Label htmlFor="service">Service</Label>
                <Select
                  value={filters.service}
                  onValueChange={(value) => setFilters({ ...filters, service: value })}
                >
                  <SelectTrigger id="service">
                    <SelectValue placeholder="All services" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All services</SelectItem>
                    <SelectItem value="web-api">Web API</SelectItem>
                    <SelectItem value="feature-engine">Feature Engine</SelectItem>
                    <SelectItem value="insight-generator">Insight Generator</SelectItem>
                    <SelectItem value="chart-renderer">Chart Renderer</SelectItem>
                    <SelectItem value="data-ingestion">Data Ingestion</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="severity">Severity</Label>
                <Select
                  value={filters.severity}
                  onValueChange={(value) => setFilters({ ...filters, severity: value })}
                >
                  <SelectTrigger id="severity">
                    <SelectValue placeholder="All severities" />
                  </SelectTrigger>
                  <SelectContent>
                    <SelectItem value="">All severities</SelectItem>
                    <SelectItem value="DEBUG">Debug</SelectItem>
                    <SelectItem value="INFO">Info</SelectItem>
                    <SelectItem value="WARNING">Warning</SelectItem>
                    <SelectItem value="ERROR">Error</SelectItem>
                    <SelectItem value="CRITICAL">Critical</SelectItem>
                  </SelectContent>
                </Select>
              </div>

              <div>
                <Label htmlFor="start-time">Start Time</Label>
                <Input
                  id="start-time"
                  type="datetime-local"
                  value={filters.start_time}
                  onChange={(e) => setFilters({ ...filters, start_time: e.target.value })}
                />
              </div>

              <div>
                <Label htmlFor="end-time">End Time</Label>
                <Input
                  id="end-time"
                  type="datetime-local"
                  value={filters.end_time}
                  onChange={(e) => setFilters({ ...filters, end_time: e.target.value })}
                />
              </div>
            </div>

            <div className="flex items-center gap-2">
              <Button type="submit" disabled={isLoading}>
                {isLoading ? (
                  <>
                    <Loader2 className="h-4 w-4 mr-2 animate-spin" />
                    Searching...
                  </>
                ) : (
                  <>
                    <Search className="h-4 w-4 mr-2" />
                    Search Logs
                  </>
                )}
              </Button>
              {logs.length > 0 && (
                <Button type="button" variant="outline" onClick={exportToCSV}>
                  <Download className="h-4 w-4 mr-2" />
                  Export CSV
                </Button>
              )}
            </div>
          </form>
        </CardContent>
      </Card>

      {/* Results */}
      <Card>
        <CardHeader>
          <CardTitle>Search Results</CardTitle>
          <CardDescription>
            {logs.length > 0 ? `Found ${logs.length} log entries` : 'No logs found'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {logs.length === 0 ? (
            <p className="text-center text-muted-foreground py-8">
              {isLoading ? 'Searching...' : 'Enter a search query and click Search Logs'}
            </p>
          ) : (
            <div className="space-y-2">
              {logs.map((log: LogEntry) => (
                <div key={log.id} className="border rounded-lg overflow-hidden">
                  <div
                    className="flex items-start gap-3 p-3 cursor-pointer hover:bg-muted/50 transition-colors"
                    onClick={() => setExpandedLog(expandedLog === log.id ? null : log.id)}
                  >
                    <Badge
                      variant="outline"
                      className={SEVERITY_COLORS[log.severity]}
                    >
                      {log.severity}
                    </Badge>
                    <div className="flex-1 min-w-0">
                      <div className="flex items-center gap-2 mb-1">
                        <span className="text-sm font-medium">{log.service}</span>
                        <span className="text-xs text-muted-foreground">
                          {format(parseISO(log.timestamp), 'MMM dd, yyyy HH:mm:ss.SSS')}
                        </span>
                      </div>
                      <p className="text-sm font-mono break-all">
                        {highlightText(log.message, searchQuery)}
                      </p>
                    </div>
                    <Button variant="ghost" size="icon" className="flex-shrink-0">
                      {expandedLog === log.id ? (
                        <ChevronUp className="h-4 w-4" />
                      ) : (
                        <ChevronDown className="h-4 w-4" />
                      )}
                    </Button>
                  </div>

                  {expandedLog === log.id && (
                    <div className="border-t bg-muted/30 p-3 space-y-3">
                      {log.metadata && (
                        <div>
                          <h4 className="text-sm font-medium mb-2">Metadata</h4>
                          <pre className="text-xs font-mono bg-background p-2 rounded overflow-x-auto">
                            {JSON.stringify(log.metadata, null, 2)}
                          </pre>
                        </div>
                      )}

                      <div>
                        <Button
                          variant="outline"
                          size="sm"
                          onClick={() => setContextLog(log.id)}
                          disabled={contextLoading && contextLog === log.id}
                        >
                          {contextLoading && contextLog === log.id ? (
                            <>
                              <Loader2 className="h-3 w-3 mr-2 animate-spin" />
                              Loading Context...
                            </>
                          ) : (
                            'Show Context'
                          )}
                        </Button>
                      </div>

                      {contextLog === log.id && contextData && (
                        <div className="space-y-1">
                          <h4 className="text-sm font-medium mb-2">Log Context</h4>
                          {contextData.logs.map((contextLog: LogEntry, index: number) => (
                            <div
                              key={contextLog.id}
                              className={`text-xs font-mono p-2 rounded ${
                                contextLog.id === log.id
                                  ? 'bg-brand/20 border border-brand'
                                  : 'bg-background'
                              }`}
                            >
                              <span className="text-muted-foreground mr-2">
                                {format(parseISO(contextLog.timestamp), 'HH:mm:ss.SSS')}
                              </span>
                              <Badge
                                variant="outline"
                                className={`${SEVERITY_COLORS[contextLog.severity]} mr-2 text-xs`}
                              >
                                {contextLog.severity}
                              </Badge>
                              {contextLog.message}
                            </div>
                          ))}
                        </div>
                      )}
                    </div>
                  )}
                </div>
              ))}
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
