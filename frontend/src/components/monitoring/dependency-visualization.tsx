'use client';

import { useEffect, useRef, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from '@/components/ui/card';
import { Badge } from '@/components/ui/badge';
import { fetchDependencyGraph } from '@/lib/api';
import { DependencyGraph, ServiceNode, ServiceEdge } from '@/types';
import { Loader2, Circle } from 'lucide-react';

const HEALTH_COLORS = {
  healthy: 'hsl(var(--miner))',
  degraded: 'hsl(var(--mempool))',
  down: 'hsl(var(--destructive))',
};

export function DependencyVisualization() {
  const canvasRef = useRef<HTMLCanvasElement>(null);
  const [selectedNode, setSelectedNode] = useState<ServiceNode | null>(null);
  const [hoveredNode, setHoveredNode] = useState<ServiceNode | null>(null);

  const { data: graphData, isLoading } = useQuery({
    queryKey: ['dependency-graph'],
    queryFn: fetchDependencyGraph,
    refetchInterval: 10000, // Refresh every 10 seconds
  });

  useEffect(() => {
    if (!graphData || !canvasRef.current) return;

    const canvas = canvasRef.current;
    const ctx = canvas.getContext('2d');
    if (!ctx) return;

    // Set canvas size
    const rect = canvas.getBoundingClientRect();
    canvas.width = rect.width * window.devicePixelRatio;
    canvas.height = rect.height * window.devicePixelRatio;
    ctx.scale(window.devicePixelRatio, window.devicePixelRatio);

    const width = rect.width;
    const height = rect.height;

    // Clear canvas
    ctx.clearRect(0, 0, width, height);

    // Calculate node positions using force-directed layout (simplified)
    const nodes = graphData.nodes.map((node: ServiceNode, index: number) => {
      const angle = (index / graphData.nodes.length) * 2 * Math.PI;
      const radius = Math.min(width, height) * 0.3;
      return {
        ...node,
        x: width / 2 + radius * Math.cos(angle),
        y: height / 2 + radius * Math.sin(angle),
      };
    });

    // Draw edges
    graphData.edges.forEach((edge: ServiceEdge) => {
      const source = nodes.find((n) => n.id === edge.source);
      const target = nodes.find((n) => n.id === edge.target);
      if (!source || !target) return;

      ctx.beginPath();
      ctx.moveTo(source.x, source.y);
      ctx.lineTo(target.x, target.y);
      
      // Color based on error rate
      const errorRate = edge.error_rate || 0;
      if (errorRate > 5) {
        ctx.strokeStyle = HEALTH_COLORS.down;
      } else if (errorRate > 1) {
        ctx.strokeStyle = HEALTH_COLORS.degraded;
      } else {
        ctx.strokeStyle = 'hsl(var(--border))';
      }
      
      ctx.lineWidth = Math.max(1, Math.min(5, edge.request_count / 100));
      ctx.stroke();

      // Draw arrow
      const angle = Math.atan2(target.y - source.y, target.x - source.x);
      const arrowSize = 8;
      const arrowX = target.x - 30 * Math.cos(angle);
      const arrowY = target.y - 30 * Math.sin(angle);

      ctx.beginPath();
      ctx.moveTo(arrowX, arrowY);
      ctx.lineTo(
        arrowX - arrowSize * Math.cos(angle - Math.PI / 6),
        arrowY - arrowSize * Math.sin(angle - Math.PI / 6)
      );
      ctx.lineTo(
        arrowX - arrowSize * Math.cos(angle + Math.PI / 6),
        arrowY - arrowSize * Math.sin(angle + Math.PI / 6)
      );
      ctx.closePath();
      ctx.fillStyle = ctx.strokeStyle;
      ctx.fill();
    });

    // Draw nodes
    nodes.forEach((node) => {
      const isSelected = selectedNode?.id === node.id;
      const isHovered = hoveredNode?.id === node.id;
      const radius = isSelected || isHovered ? 30 : 25;

      // Node circle
      ctx.beginPath();
      ctx.arc(node.x, node.y, radius, 0, 2 * Math.PI);
      ctx.fillStyle = HEALTH_COLORS[node.health_status];
      ctx.fill();
      
      if (isSelected || isHovered) {
        ctx.strokeStyle = 'hsl(var(--brand))';
        ctx.lineWidth = 3;
        ctx.stroke();
      }

      // Node label
      ctx.fillStyle = 'hsl(var(--foreground))';
      ctx.font = '12px Inter, sans-serif';
      ctx.textAlign = 'center';
      ctx.textBaseline = 'middle';
      
      const lines = node.name.split('-');
      lines.forEach((line, i) => {
        ctx.fillText(line, node.x, node.y + radius + 15 + i * 14);
      });
    });

    // Handle canvas clicks
    const handleClick = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      const clickedNode = nodes.find((node) => {
        const distance = Math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2);
        return distance < 30;
      });

      setSelectedNode(clickedNode || null);
    };

    const handleMouseMove = (event: MouseEvent) => {
      const rect = canvas.getBoundingClientRect();
      const x = event.clientX - rect.left;
      const y = event.clientY - rect.top;

      const hoveredNode = nodes.find((node) => {
        const distance = Math.sqrt((node.x - x) ** 2 + (node.y - y) ** 2);
        return distance < 30;
      });

      setHoveredNode(hoveredNode || null);
      canvas.style.cursor = hoveredNode ? 'pointer' : 'default';
    };

    canvas.addEventListener('click', handleClick);
    canvas.addEventListener('mousemove', handleMouseMove);

    return () => {
      canvas.removeEventListener('click', handleClick);
      canvas.removeEventListener('mousemove', handleMouseMove);
    };
  }, [graphData, selectedNode, hoveredNode]);

  if (isLoading) {
    return (
      <Card>
        <CardContent className="flex items-center justify-center h-96">
          <Loader2 className="h-8 w-8 animate-spin text-muted-foreground" />
        </CardContent>
      </Card>
    );
  }

  return (
    <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
      {/* Visualization */}
      <Card className="lg:col-span-2">
        <CardHeader>
          <CardTitle>Service Dependency Graph</CardTitle>
          <CardDescription>
            Real-time visualization of service connections and health status
          </CardDescription>
        </CardHeader>
        <CardContent>
          <div className="relative">
            <canvas
              ref={canvasRef}
              className="w-full h-[500px] border rounded-lg bg-background"
            />
            <div className="absolute top-4 right-4 flex items-center gap-4 bg-card/80 backdrop-blur-sm p-3 rounded-lg border">
              <div className="flex items-center gap-2">
                <Circle className="h-3 w-3 fill-success text-success" />
                <span className="text-xs">Healthy</span>
              </div>
              <div className="flex items-center gap-2">
                <Circle className="h-3 w-3 fill-warning text-warning" />
                <span className="text-xs">Degraded</span>
              </div>
              <div className="flex items-center gap-2">
                <Circle className="h-3 w-3 fill-destructive text-destructive" />
                <span className="text-xs">Down</span>
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Service Details */}
      <Card>
        <CardHeader>
          <CardTitle>Service Details</CardTitle>
          <CardDescription>
            {selectedNode ? 'Selected service information' : 'Click a node to view details'}
          </CardDescription>
        </CardHeader>
        <CardContent>
          {selectedNode ? (
            <div className="space-y-4">
              <div>
                <h3 className="font-semibold text-lg mb-2">{selectedNode.name}</h3>
                <Badge
                  variant="outline"
                  className={
                    selectedNode.health_status === 'healthy'
                      ? 'bg-success'
                      : selectedNode.health_status === 'degraded'
                      ? 'bg-warning'
                      : 'bg-destructive'
                  }
                >
                  {selectedNode.health_status}
                </Badge>
              </div>

              {selectedNode.cpu_usage !== undefined && (
                <div>
                  <p className="text-sm text-muted-foreground">CPU Usage</p>
                  <p className="text-2xl font-semibold">
                    {selectedNode.cpu_usage.toFixed(1)}%
                  </p>
                </div>
              )}

              {selectedNode.memory_usage !== undefined && (
                <div>
                  <p className="text-sm text-muted-foreground">Memory Usage</p>
                  <p className="text-2xl font-semibold">
                    {selectedNode.memory_usage.toFixed(1)}%
                  </p>
                </div>
              )}

              <div className="pt-4 border-t">
                <h4 className="font-medium mb-2">Dependencies</h4>
                <div className="space-y-2">
                  {graphData?.edges
                    .filter((edge: ServiceEdge) => edge.source === selectedNode.id)
                    .map((edge: ServiceEdge) => {
                      const target = graphData.nodes.find(
                        (n: ServiceNode) => n.id === edge.target
                      );
                      return (
                        <div
                          key={edge.target}
                          className="flex items-center justify-between text-sm"
                        >
                          <span>{target?.name}</span>
                          <div className="flex items-center gap-2">
                            <span className="text-muted-foreground">
                              {edge.request_count} req/min
                            </span>
                            {edge.error_rate > 0 && (
                              <Badge variant="destructive" className="text-xs">
                                {edge.error_rate.toFixed(1)}% errors
                              </Badge>
                            )}
                          </div>
                        </div>
                      );
                    })}
                </div>
              </div>

              <div className="pt-4 border-t">
                <h4 className="font-medium mb-2">Dependents</h4>
                <div className="space-y-2">
                  {graphData?.edges
                    .filter((edge: ServiceEdge) => edge.target === selectedNode.id)
                    .map((edge: ServiceEdge) => {
                      const source = graphData.nodes.find(
                        (n: ServiceNode) => n.id === edge.source
                      );
                      return (
                        <div
                          key={edge.source}
                          className="flex items-center justify-between text-sm"
                        >
                          <span>{source?.name}</span>
                          <span className="text-muted-foreground">
                            {edge.avg_latency.toFixed(0)}ms avg
                          </span>
                        </div>
                      );
                    })}
                </div>
              </div>
            </div>
          ) : (
            <div className="text-center py-12">
              <p className="text-muted-foreground">
                Select a service node to view detailed information
              </p>
            </div>
          )}
        </CardContent>
      </Card>
    </div>
  );
}
