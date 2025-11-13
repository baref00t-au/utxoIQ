# Design Document

## Overview

This design implements comprehensive UI/UX enhancements focusing on customization, accessibility, responsive design, and user productivity. The system uses React DnD for drag-and-drop, CSS variables for theming, TanStack Table for advanced data tables, and follows WCAG 2.1 AA accessibility guidelines.

## Architecture

### Component Architecture

```
┌─────────────────────────────────────────┐
│         App Layout (Root)               │
│  - Theme Provider                       │
│  - Auth Context                         │
│  - Keyboard Shortcut Handler            │
└────────────┬────────────────────────────┘
             │
    ┌────────┴────────┐
    │                 │
┌───▼────┐      ┌────▼─────┐
│ Header │      │  Main    │
│ - Theme│      │  Content │
│ - Nav  │      └────┬─────┘
└────────┘           │
              ┌──────┴──────┐
              │             │
        ┌─────▼──┐    ┌────▼─────┐
        │Dashboard│    │ Insights │
        │ (DnD)  │    │ (Filters)│
        └────────┘    └──────────┘
```

## Components and Interfaces

### 1. Theme System

#### Theme Provider
```typescript
// lib/theme.tsx
import { createContext, useContext, useEffect, useState } from 'react';

type Theme = 'light' | 'dark';

interface ThemeContextType {
  theme: Theme;
  toggleTheme: () => void;
  setTheme: (theme: Theme) => void;
}

const ThemeContext = createContext<ThemeContextType | undefined>(undefined);

export function ThemeProvider({ children }: { children: React.ReactNode }) {
  const [theme, setThemeState] = useState<Theme>('dark');
  
  useEffect(() => {
    // Load saved theme from localStorage
    const saved = localStorage.getItem('theme') as Theme;
    if (saved) {
      setThemeState(saved);
    } else {
      // Detect system preference
      const prefersDark = window.matchMedia('(prefers-color-scheme: dark)').matches;
      setThemeState(prefersDark ? 'dark' : 'light');
    }
  }, []);
  
  useEffect(() => {
    // Apply theme to document
    document.documentElement.setAttribute('data-theme', theme);
    localStorage.setItem('theme', theme);
  }, [theme]);
  
  const toggleTheme = () => {
    setThemeState(prev => prev === 'dark' ? 'light' : 'dark');
  };
  
  const setTheme = (newTheme: Theme) => {
    setThemeState(newTheme);
  };
  
  return (
    <ThemeContext.Provider value={{ theme, toggleTheme, setTheme }}>
      {children}
    </ThemeContext.Provider>
  );
}

export const useTheme = () => {
  const context = useContext(ThemeContext);
  if (!context) throw new Error('useTheme must be used within ThemeProvider');
  return context;
};
```

#### CSS Variables for Theming
```css
/* globals.css */
:root[data-theme="dark"] {
  --background: #0B0B0C;
  --surface: #131316;
  --border: #2A2A2E;
  --text-primary: #F4F4F5;
  --text-secondary: #A1A1AA;
  --brand: #FF5A21;
  --success: #16A34A;
  --warning: #D97706;
  --error: #DC2626;
}

:root[data-theme="light"] {
  --background: #FFFFFF;
  --surface: #F9FAFB;
  --border: #E5E7EB;
  --text-primary: #111827;
  --text-secondary: #6B7280;
  --brand: #FF5A21;
  --success: #16A34A;
  --warning: #D97706;
  --error: #DC2626;
}
```

### 2. Drag-and-Drop Dashboard

#### Dashboard Layout Component
```typescript
// components/DashboardLayout.tsx
import { DndContext, DragEndEvent, closestCenter } from '@dnd-kit/core';
import { SortableContext, rectSortingStrategy } from '@dnd-kit/sortable';
import { useSortable } from '@dnd-kit/sortable';
import { CSS } from '@dnd-kit/utilities';

interface Widget {
  id: string;
  type: string;
  title: string;
  config: Record<string, any>;
  position: { x: number; y: number; w: number; h: number };
}

interface DashboardLayoutProps {
  widgets: Widget[];
  onLayoutChange: (widgets: Widget[]) => void;
}

export function DashboardLayout({ widgets, onLayoutChange }: DashboardLayoutProps) {
  const handleDragEnd = (event: DragEndEvent) => {
    const { active, over } = event;
    
    if (over && active.id !== over.id) {
      const oldIndex = widgets.findIndex(w => w.id === active.id);
      const newIndex = widgets.findIndex(w => w.id === over.id);
      
      const newWidgets = arrayMove(widgets, oldIndex, newIndex);
      onLayoutChange(newWidgets);
    }
  };
  
  return (
    <DndContext collisionDetection={closestCenter} onDragEnd={handleDragEnd}>
      <SortableContext items={widgets.map(w => w.id)} strategy={rectSortingStrategy}>
        <div className="grid grid-cols-12 gap-4">
          {widgets.map(widget => (
            <SortableWidget key={widget.id} widget={widget} />
          ))}
        </div>
      </SortableContext>
    </DndContext>
  );
}

function SortableWidget({ widget }: { widget: Widget }) {
  const { attributes, listeners, setNodeRef, transform, transition } = useSortable({
    id: widget.id
  });
  
  const style = {
    transform: CSS.Transform.toString(transform),
    transition,
    gridColumn: `span ${widget.position.w}`,
    gridRow: `span ${widget.position.h}`,
  };
  
  return (
    <div ref={setNodeRef} style={style} {...attributes} {...listeners}>
      <WidgetRenderer widget={widget} />
    </div>
  );
}
```

### 3. Advanced Filtering System

#### Filter Component
```typescript
// components/InsightFilters.tsx
import { useState } from 'react';
import { useDebounce } from '@/hooks/useDebounce';

interface FilterState {
  search: string;
  categories: string[];
  minConfidence: number;
  dateRange: { start: Date; end: Date } | null;
}

interface InsightFiltersProps {
  onFilterChange: (filters: FilterState) => void;
  resultCount: number;
}

export function InsightFilters({ onFilterChange, resultCount }: InsightFiltersProps) {
  const [filters, setFilters] = useState<FilterState>({
    search: '',
    categories: [],
    minConfidence: 0,
    dateRange: null,
  });
  
  const debouncedFilters = useDebounce(filters, 300);
  
  useEffect(() => {
    onFilterChange(debouncedFilters);
  }, [debouncedFilters]);
  
  return (
    <div className="space-y-4">
      <Input
        placeholder="Search insights..."
        value={filters.search}
        onChange={(e) => setFilters(prev => ({ ...prev, search: e.target.value }))}
        aria-label="Search insights"
      />
      
      <CategorySelect
        selected={filters.categories}
        onChange={(categories) => setFilters(prev => ({ ...prev, categories }))}
      />
      
      <ConfidenceSlider
        value={filters.minConfidence}
        onChange={(minConfidence) => setFilters(prev => ({ ...prev, minConfidence }))}
      />
      
      <DateRangePicker
        value={filters.dateRange}
        onChange={(dateRange) => setFilters(prev => ({ ...prev, dateRange }))}
      />
      
      <div className="text-sm text-secondary">
        {resultCount} results
      </div>
    </div>
  );
}
```

#### Filter Presets
```typescript
// components/FilterPresets.tsx
interface FilterPreset {
  id: string;
  name: string;
  filters: FilterState;
}

export function FilterPresets() {
  const [presets, setPresets] = useState<FilterPreset[]>([]);
  const [showSaveDialog, setShowSaveDialog] = useState(false);
  
  const savePreset = async (name: string, filters: FilterState) => {
    const response = await fetch('/api/v1/filters/presets', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ name, filters })
    });
    
    const preset = await response.json();
    setPresets(prev => [...prev, preset]);
  };
  
  const applyPreset = (preset: FilterPreset) => {
    onFilterChange(preset.filters);
  };
  
  return (
    <div className="space-y-2">
      <h3 className="text-sm font-medium">Saved Filters</h3>
      {presets.map(preset => (
        <button
          key={preset.id}
          onClick={() => applyPreset(preset)}
          className="w-full text-left px-3 py-2 rounded hover:bg-surface"
        >
          {preset.name}
        </button>
      ))}
      <button onClick={() => setShowSaveDialog(true)}>
        Save Current Filters
      </button>
    </div>
  );
}
```

### 4. Data Export System

```typescript
// lib/export.ts
export async function exportToCSV(data: any[], filename: string) {
  const csv = convertToCSV(data);
  const blob = new Blob([csv], { type: 'text/csv' });
  downloadBlob(blob, `${filename}.csv`);
}

export async function exportToJSON(data: any[], filename: string) {
  const json = JSON.stringify(data, null, 2);
  const blob = new Blob([json], { type: 'application/json' });
  downloadBlob(blob, `${filename}.json`);
}

function convertToCSV(data: any[]): string {
  if (data.length === 0) return '';
  
  const headers = Object.keys(data[0]);
  const rows = data.map(row => 
    headers.map(header => {
      const value = row[header];
      return typeof value === 'string' && value.includes(',') 
        ? `"${value}"` 
        : value;
    }).join(',')
  );
  
  return [headers.join(','), ...rows].join('\n');
}

function downloadBlob(blob: Blob, filename: string) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}
```

### 5. Bookmark System

#### Database Model
```python
class Bookmark(Base):
    __tablename__ = "bookmarks"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    insight_id = Column(String(100), nullable=False)
    folder_id = Column(UUID, ForeignKey('bookmark_folders.id'), nullable=True)
    note = Column(Text, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="bookmarks")
    folder = relationship("BookmarkFolder", backref="bookmarks")
    
    __table_args__ = (
        Index('idx_bookmark_user', 'user_id'),
        UniqueConstraint('user_id', 'insight_id', name='uq_user_insight_bookmark'),
    )

class BookmarkFolder(Base):
    __tablename__ = "bookmark_folders"
    
    id = Column(UUID, primary_key=True, default=uuid4)
    user_id = Column(UUID, ForeignKey('users.id'), nullable=False)
    name = Column(String(100), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    
    user = relationship("User", backref="bookmark_folders")
```

### 6. Interactive Charts

```typescript
// components/InteractiveChart.tsx
import { LineChart, Line, XAxis, YAxis, Tooltip, ResponsiveContainer } from 'recharts';
import { useState } from 'react';

export function InteractiveChart({ data }: { data: any[] }) {
  const [zoomDomain, setZoomDomain] = useState<[number, number] | null>(null);
  
  const handleZoom = (e: any) => {
    if (e.activeLabel) {
      // Implement zoom logic
    }
  };
  
  const resetZoom = () => {
    setZoomDomain(null);
  };
  
  const exportToPNG = async () => {
    const chartElement = document.getElementById('chart');
    if (!chartElement) return;
    
    const canvas = await html2canvas(chartElement, { scale: 2 });
    const url = canvas.toDataURL('image/png');
    
    const a = document.createElement('a');
    a.href = url;
    a.download = `chart-${Date.now()}.png`;
    a.click();
  };
  
  return (
    <div>
      <div className="flex gap-2 mb-4">
        <button onClick={resetZoom}>Reset Zoom</button>
        <button onClick={exportToPNG}>Export PNG</button>
      </div>
      
      <div id="chart">
        <ResponsiveContainer width="100%" height={400}>
          <LineChart data={data} onMouseDown={handleZoom}>
            <XAxis dataKey="timestamp" />
            <YAxis />
            <Tooltip />
            <Line type="monotone" dataKey="value" stroke="var(--brand)" />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </div>
  );
}
```

### 7. Keyboard Shortcuts

```typescript
// hooks/useKeyboardShortcuts.ts
import { useEffect } from 'react';

interface Shortcut {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  action: () => void;
  description: string;
}

export function useKeyboardShortcuts(shortcuts: Shortcut[]) {
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const ctrlMatch = shortcut.ctrl ? e.ctrlKey || e.metaKey : !e.ctrlKey && !e.metaKey;
        const shiftMatch = shortcut.shift ? e.shiftKey : !e.shiftKey;
        
        if (e.key === shortcut.key && ctrlMatch && shiftMatch) {
          e.preventDefault();
          shortcut.action();
          break;
        }
      }
    };
    
    window.addEventListener('keydown', handleKeyDown);
    return () => window.removeEventListener('keydown', handleKeyDown);
  }, [shortcuts]);
}

// Usage
export function App() {
  const shortcuts = [
    { key: '/', action: () => focusSearch(), description: 'Focus search' },
    { key: '?', action: () => showHelp(), description: 'Show shortcuts' },
    { key: 'Escape', action: () => closeModal(), description: 'Close modal' },
  ];
  
  useKeyboardShortcuts(shortcuts);
  
  return <div>...</div>;
}
```

### 8. Responsive Design

```css
/* Responsive breakpoints */
@media (max-width: 639px) {
  /* Mobile */
  .dashboard-grid {
    grid-template-columns: 1fr;
  }
  
  .nav-menu {
    display: none;
  }
  
  .hamburger-menu {
    display: block;
  }
}

@media (min-width: 640px) and (max-width: 1023px) {
  /* Tablet */
  .dashboard-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}

@media (min-width: 1024px) {
  /* Desktop */
  .dashboard-grid {
    grid-template-columns: repeat(4, 1fr);
  }
}
```

### 9. Accessibility Features

```typescript
// components/AccessibleButton.tsx
export function AccessibleButton({
  children,
  onClick,
  ariaLabel,
  disabled = false
}: {
  children: React.ReactNode;
  onClick: () => void;
  ariaLabel: string;
  disabled?: boolean;
}) {
  return (
    <button
      onClick={onClick}
      disabled={disabled}
      aria-label={ariaLabel}
      className="focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
      tabIndex={0}
    >
      {children}
    </button>
  );
}

// Skip to main content link
export function SkipToMain() {
  return (
    <a
      href="#main-content"
      className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-50 focus:px-4 focus:py-2 focus:bg-brand focus:text-white"
    >
      Skip to main content
    </a>
  );
}
```

## Testing Strategy

### Unit Tests
- Theme switching logic
- Filter state management
- Export data formatting
- Keyboard shortcut handling

### Integration Tests
- Drag-and-drop dashboard layout
- Filter application and result updates
- Bookmark creation and organization
- Chart interactions and exports

### Accessibility Tests
- Keyboard navigation through all pages
- Screen reader compatibility
- Color contrast validation
- Focus indicator visibility

### Responsive Tests
- Layout adaptation at all breakpoints
- Touch target sizes on mobile
- Performance on mobile networks

## Configuration

### Tailwind Configuration
```javascript
// tailwind.config.js
module.exports = {
  theme: {
    extend: {
      colors: {
        background: 'var(--background)',
        surface: 'var(--surface)',
        border: 'var(--border)',
        'text-primary': 'var(--text-primary)',
        'text-secondary': 'var(--text-secondary)',
        brand: 'var(--brand)',
      },
      screens: {
        'xs': '320px',
        'sm': '640px',
        'md': '768px',
        'lg': '1024px',
        'xl': '1280px',
        '2xl': '1536px',
      },
    },
  },
};
```

## Deployment Considerations

### Performance Optimization
- Lazy load dashboard widgets
- Virtualize long lists with TanStack Virtual
- Debounce filter inputs
- Cache filter results in React Query

### Accessibility Compliance
- Run automated accessibility tests in CI
- Manual testing with screen readers
- Keyboard navigation testing
- Color contrast validation

### Mobile Optimization
- Optimize images for mobile
- Reduce JavaScript bundle size
- Use responsive images with srcset
- Implement service worker for offline support
