'use client';

import { useState, useRef, useCallback } from 'react';
import {
  LineChart,
  Line,
  XAxis,
  YAxis,
  CartesianGrid,
  Tooltip,
  ResponsiveContainer,
  ReferenceArea,
} from 'recharts';
import { Button } from '@/components/ui/button';
import { Download, RotateCcw, Image as ImageIcon, FileCode } from 'lucide-react';
import html2canvas from 'html2canvas';
import { useTheme } from '@/lib/theme';
import {
  DropdownMenu,
  DropdownMenuContent,
  DropdownMenuItem,
  DropdownMenuTrigger,
} from '@/components/ui/dropdown-menu';

export interface ChartDataPoint {
  timestamp: string | number;
  value: number;
  [key: string]: any;
}

export interface InteractiveChartProps {
  data: ChartDataPoint[];
  title?: string;
  dataKey?: string;
  xAxisKey?: string;
  height?: number;
  showGrid?: boolean;
  strokeColor?: string;
}

export function InteractiveChart({
  data,
  title = 'Chart',
  dataKey = 'value',
  xAxisKey = 'timestamp',
  height = 400,
  showGrid = true,
  strokeColor,
}: InteractiveChartProps) {
  const { theme } = useTheme();
  const chartRef = useRef<HTMLDivElement>(null);
  
  // Zoom and pan state
  const [zoomState, setZoomState] = useState<{
    left: number | string;
    right: number | string;
  } | null>(null);
  const [refAreaLeft, setRefAreaLeft] = useState<string | number>('');
  const [refAreaRight, setRefAreaRight] = useState<string | number>('');
  const [isSelecting, setIsSelecting] = useState(false);

  // Get initial data domain
  const getAxisDomain = useCallback((): [string | number, string | number] => {
    if (zoomState) {
      return [zoomState.left, zoomState.right];
    }
    return ['auto', 'auto'];
  }, [zoomState]);

  // Handle mouse down for zoom selection
  const handleMouseDown = (e: any) => {
    if (e && e.activeLabel) {
      setRefAreaLeft(e.activeLabel);
      setIsSelecting(true);
    }
  };

  // Handle mouse move during selection
  const handleMouseMove = (e: any) => {
    if (isSelecting && e && e.activeLabel) {
      setRefAreaRight(e.activeLabel);
    }
  };

  // Handle mouse up to complete zoom
  const handleMouseUp = () => {
    if (!isSelecting) return;
    
    setIsSelecting(false);

    if (refAreaLeft === refAreaRight || refAreaRight === '') {
      setRefAreaLeft('');
      setRefAreaRight('');
      return;
    }

    // Ensure left is less than right
    let left = refAreaLeft;
    let right = refAreaRight;

    if (left > right) {
      [left, right] = [right, left];
    }

    setZoomState({ left, right });
    setRefAreaLeft('');
    setRefAreaRight('');
  };

  // Reset zoom to show all data
  const handleResetZoom = () => {
    setZoomState(null);
    setRefAreaLeft('');
    setRefAreaRight('');
  };

  // Export chart as PNG
  const exportToPNG = async () => {
    if (!chartRef.current) return;

    try {
      const canvas = await html2canvas(chartRef.current, {
        scale: 2,
        backgroundColor: theme === 'dark' ? '#0B0B0C' : '#FFFFFF',
        logging: false,
      });

      const url = canvas.toDataURL('image/png');
      const link = document.createElement('a');
      const timestamp = new Date().toISOString().split('T')[0];
      link.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${timestamp}.png`;
      link.href = url;
      link.click();
    } catch (error) {
      console.error('Failed to export chart as PNG:', error);
    }
  };

  // Export chart as SVG
  const exportToSVG = () => {
    if (!chartRef.current) return;

    try {
      const svgElement = chartRef.current.querySelector('svg');
      if (!svgElement) return;

      // Clone the SVG to avoid modifying the original
      const clonedSvg = svgElement.cloneNode(true) as SVGElement;
      
      // Add title and timestamp
      const titleElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      titleElement.setAttribute('x', '10');
      titleElement.setAttribute('y', '20');
      titleElement.setAttribute('font-size', '16');
      titleElement.setAttribute('font-weight', 'bold');
      titleElement.setAttribute('fill', theme === 'dark' ? '#F4F4F5' : '#111827');
      titleElement.textContent = title;
      
      const timestampElement = document.createElementNS('http://www.w3.org/2000/svg', 'text');
      timestampElement.setAttribute('x', '10');
      timestampElement.setAttribute('y', '40');
      timestampElement.setAttribute('font-size', '12');
      timestampElement.setAttribute('fill', theme === 'dark' ? '#A1A1AA' : '#6B7280');
      timestampElement.textContent = new Date().toLocaleString();
      
      clonedSvg.insertBefore(timestampElement, clonedSvg.firstChild);
      clonedSvg.insertBefore(titleElement, clonedSvg.firstChild);

      // Serialize SVG to string
      const serializer = new XMLSerializer();
      const svgString = serializer.serializeToString(clonedSvg);
      
      // Create blob and download
      const blob = new Blob([svgString], { type: 'image/svg+xml' });
      const url = URL.createObjectURL(blob);
      const link = document.createElement('a');
      const timestamp = new Date().toISOString().split('T')[0];
      link.download = `${title.toLowerCase().replace(/\s+/g, '-')}-${timestamp}.svg`;
      link.href = url;
      link.click();
      URL.revokeObjectURL(url);
    } catch (error) {
      console.error('Failed to export chart as SVG:', error);
    }
  };

  // Get theme-aware colors
  const getChartColors = () => {
    if (theme === 'dark') {
      return {
        stroke: strokeColor || '#FF5A21',
        grid: '#2A2A2E',
        text: '#A1A1AA',
        tooltip: '#131316',
        tooltipBorder: '#2A2A2E',
      };
    }
    return {
      stroke: strokeColor || '#FF5A21',
      grid: '#E5E7EB',
      text: '#6B7280',
      tooltip: '#FFFFFF',
      tooltipBorder: '#E5E7EB',
    };
  };

  const colors = getChartColors();

  return (
    <div className="space-y-4">
      {/* Chart controls */}
      <div className="flex items-center justify-between">
        <h3 className="text-lg font-semibold">{title}</h3>
        <div className="flex gap-2">
          <Button
            variant="outline"
            size="sm"
            onClick={handleResetZoom}
            disabled={!zoomState}
            aria-label="Reset zoom"
          >
            <RotateCcw className="h-4 w-4 mr-2" />
            Reset Zoom
          </Button>
          
          <DropdownMenu>
            <DropdownMenuTrigger asChild>
              <Button variant="outline" size="sm" aria-label="Export chart">
                <Download className="h-4 w-4 mr-2" />
                Export
              </Button>
            </DropdownMenuTrigger>
            <DropdownMenuContent align="end">
              <DropdownMenuItem onClick={exportToPNG}>
                <ImageIcon className="h-4 w-4 mr-2" />
                Export as PNG
              </DropdownMenuItem>
              <DropdownMenuItem onClick={exportToSVG}>
                <FileCode className="h-4 w-4 mr-2" />
                Export as SVG
              </DropdownMenuItem>
            </DropdownMenuContent>
          </DropdownMenu>
        </div>
      </div>

      {/* Chart container */}
      <div
        ref={chartRef}
        className="rounded-lg border border-border bg-surface p-4"
        style={{ cursor: isSelecting ? 'crosshair' : 'default' }}
      >
        <ResponsiveContainer width="100%" height={height}>
          <LineChart
            data={data}
            onMouseDown={handleMouseDown}
            onMouseMove={handleMouseMove}
            onMouseUp={handleMouseUp}
          >
            {showGrid && (
              <CartesianGrid strokeDasharray="3 3" stroke={colors.grid} />
            )}
            
            <XAxis
              dataKey={xAxisKey}
              stroke={colors.text}
              tick={{ fill: colors.text }}
              domain={getAxisDomain()}
              allowDataOverflow
            />
            
            <YAxis
              stroke={colors.text}
              tick={{ fill: colors.text }}
            />
            
            <Tooltip
              contentStyle={{
                backgroundColor: colors.tooltip,
                border: `1px solid ${colors.tooltipBorder}`,
                borderRadius: '8px',
                color: theme === 'dark' ? '#F4F4F5' : '#111827',
              }}
              cursor={{ stroke: colors.stroke, strokeWidth: 1, strokeDasharray: '3 3' }}
            />
            
            <Line
              type="monotone"
              dataKey={dataKey}
              stroke={colors.stroke}
              strokeWidth={2}
              dot={false}
              animationDuration={300}
            />
            
            {/* Selection area for zooming */}
            {refAreaLeft && refAreaRight && (
              <ReferenceArea
                x1={refAreaLeft}
                x2={refAreaRight}
                strokeOpacity={0.3}
                fill={colors.stroke}
                fillOpacity={0.1}
              />
            )}
          </LineChart>
        </ResponsiveContainer>
      </div>

      {/* Instructions */}
      <p className="text-sm text-muted-foreground">
        Click and drag to zoom into a specific area. Use the Reset Zoom button to view all data.
      </p>
    </div>
  );
}
