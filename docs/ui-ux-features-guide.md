# UI/UX Features Guide

## Overview

This guide provides a comprehensive overview of all user interface and user experience enhancements implemented in utxoIQ. These features improve usability, accessibility, and productivity for all users.

## Quick Links

- **Frontend Documentation**: [frontend/docs/README.md](../frontend/docs/README.md)
- **Accessibility**: [frontend/docs/ACCESSIBILITY.md](../frontend/docs/ACCESSIBILITY.md)
- **Theme System**: [frontend/docs/THEME_CUSTOMIZATION.md](../frontend/docs/THEME_CUSTOMIZATION.md)
- **Dashboard**: [frontend/docs/DASHBOARD_CUSTOMIZATION.md](../frontend/docs/DASHBOARD_CUSTOMIZATION.md)
- **Filters**: [frontend/docs/FILTER_PRESETS.md](../frontend/docs/FILTER_PRESETS.md)
- **Export**: [frontend/docs/DATA_EXPORT.md](../frontend/docs/DATA_EXPORT.md)
- **Shortcuts**: [frontend/docs/KEYBOARD_SHORTCUTS.md](../frontend/docs/KEYBOARD_SHORTCUTS.md)

## Feature Summary

### 1. Theme System

**Status**: ✅ Implemented  
**Location**: `frontend/src/lib/theme.tsx`

#### Features
- Dark theme (default) and light theme
- CSS variables for all color tokens
- Automatic persistence in localStorage
- System preference detection
- Smooth theme transitions (200ms)

#### Usage
```typescript
import { useTheme } from '@/lib/theme';

const { theme, toggleTheme, setTheme } = useTheme();
```

#### Documentation
- [Theme Customization Guide](../frontend/docs/THEME_CUSTOMIZATION.md)

---

### 2. Drag-and-Drop Dashboard

**Status**: ✅ Implemented  
**Location**: `frontend/src/components/dashboard/`

#### Features
- Drag-and-drop widget repositioning
- Widget resizing with corner handles
- Grid-based snapping (12 columns)
- Auto-save layout changes (2s delay)
- Widget library with 8+ widget types
- Layout export/import
- Responsive design (mobile, tablet, desktop)

#### Usage
```typescript
import { DashboardLayout } from '@/components/dashboard/dashboard-layout';

<DashboardLayout widgets={widgets} onLayoutChange={handleChange} />
```

#### Documentation
- [Dashboard Customization Guide](../frontend/docs/DASHBOARD_CUSTOMIZATION.md)

---

### 3. Advanced Filtering System

**Status**: ✅ Implemented  
**Location**: `frontend/src/components/insights/insight-filters.tsx`

#### Features
- Full-text search with debouncing (300ms)
- Category filters (Mempool, Exchange, Miner, Whale)
- Confidence threshold slider
- Date range picker
- Filter result count preview
- URL persistence of filter state
- Apply filters within 500ms

#### Usage
```typescript
import { InsightFilters } from '@/components/insights/insight-filters';

<InsightFilters onFilterChange={handleFilterChange} resultCount={count} />
```

#### Documentation
- [Filter Presets Guide](../frontend/docs/FILTER_PRESETS.md)

---

### 4. Filter Presets

**Status**: ✅ Implemented  
**Location**: `frontend/src/components/insights/filter-presets.tsx`

#### Features
- Save filter combinations with custom names
- Store up to 10 presets per user (Pro tier)
- One-click preset application
- Edit and delete presets
- Preset export/import (Pro/Power tier)
- Preset sharing (Power tier)

#### API Endpoints
```
POST   /api/v1/filters/presets
GET    /api/v1/filters/presets
PUT    /api/v1/filters/presets/:id
DELETE /api/v1/filters/presets/:id
```

#### Documentation
- [Filter Presets Guide](../frontend/docs/FILTER_PRESETS.md)

---

### 5. Data Export System

**Status**: ✅ Implemented  
**Location**: `frontend/src/lib/export.ts`

#### Features
- CSV export for Excel/Sheets
- JSON export for programming
- Export up to 1,000 rows (Pro tier)
- Batch export multiple filters
- Scheduled exports (Power tier)
- API export for automation
- Filename includes filter criteria and timestamp

#### Export Formats

**CSV Structure**:
```csv
id,category,headline,summary,confidence,createdAt,blockHeight,txCount
```

**JSON Structure**:
```json
[
  {
    "id": "insight-001",
    "category": "mempool",
    "headline": "High Fee Environment",
    "confidence": 0.87,
    "evidence": { "blocks": [...], "txids": [...] }
  }
]
```

#### Documentation
- [Data Export Guide](../frontend/docs/DATA_EXPORT.md)

---

### 6. Bookmark System

**Status**: ✅ Implemented  
**Location**: `frontend/src/components/insights/bookmark-button.tsx`

#### Features
- One-click bookmark insights
- Add notes to bookmarks
- Organize bookmarks into folders
- Sync across devices
- Optimistic updates for instant feedback
- Offline bookmark creation

#### Database Schema
```python
class Bookmark(Base):
    id = Column(UUID, primary_key=True)
    user_id = Column(UUID, ForeignKey('users.id'))
    insight_id = Column(String(100))
    folder_id = Column(UUID, ForeignKey('bookmark_folders.id'))
    note = Column(Text)
    created_at = Column(DateTime)
```

---

### 7. Interactive Charts

**Status**: ✅ Implemented  
**Location**: `frontend/src/components/charts/interactive-chart.tsx`

#### Features
- Mouse wheel zoom
- Click-and-drag panning
- Reset zoom button
- Crosshair with value tooltips
- PNG export at 2x resolution
- SVG export for vector graphics
- Theme-aware colors

#### Usage
```typescript
import { InteractiveChart } from '@/components/charts/interactive-chart';

<InteractiveChart data={data} />
```

---

### 8. Sortable Data Tables

**Status**: ✅ Implemented  
**Location**: `frontend/src/components/tables/sortable-table.tsx`

#### Features
- Single-column sorting
- Multi-column sorting (Shift + Click)
- Sort indicators with arrows
- Virtualization for large datasets
- Sort within 200ms for 10,000 rows
- Maintain sort state when filtering

#### Usage
```typescript
import { SortableTable } from '@/components/tables/sortable-table';

<SortableTable columns={columns} data={data} />
```

---

### 9. Keyboard Shortcuts

**Status**: ✅ Implemented  
**Location**: `frontend/src/hooks/use-keyboard-shortcuts.ts`

#### Features
- 50+ keyboard shortcuts
- Global shortcuts (?, /, Escape)
- Navigation shortcuts (G then F/B/A/C/D)
- Feature-specific shortcuts
- Customizable shortcuts (Power tier)
- Help modal (press ?)

#### Common Shortcuts
- **?**: Show shortcuts help
- **/**: Focus search
- **Escape**: Close modals
- **J/K**: Navigate lists
- **Ctrl/Cmd + S**: Save
- **Ctrl/Cmd + /**: Toggle theme

#### Documentation
- [Keyboard Shortcuts Reference](../frontend/docs/KEYBOARD_SHORTCUTS.md)

---

### 10. Responsive Design

**Status**: ✅ Implemented  
**Location**: `frontend/src/app/globals.css`

#### Features
- Mobile-first approach
- Breakpoints: 320px, 640px, 768px, 1024px
- Touch-friendly controls (44×44px minimum)
- Hamburger menu on mobile
- Vertical widget stacking on mobile
- Optimized for 3G connections

#### Breakpoints
```css
/* Mobile: ≤ 639px */
/* Tablet: 640px - 1023px */
/* Desktop: ≥ 1024px */
```

---

### 11. Accessibility Features

**Status**: ✅ Implemented  
**Location**: Multiple components

#### Features
- WCAG 2.1 AA compliant
- Keyboard navigation for all features
- Screen reader support (NVDA, JAWS, VoiceOver)
- ARIA labels for all icons and buttons
- Color contrast 4.5:1 minimum
- Visible focus indicators
- Skip to main content link
- Reduced motion support

#### Testing
```bash
# Run accessibility tests
npm run test:e2e -- tests/accessibility.spec.ts

# Automated testing with axe-core
npm test -- accessibility.test.tsx
```

#### Documentation
- [Accessibility Guide](../frontend/docs/ACCESSIBILITY.md)

---

## Implementation Status

| Feature | Status | Tests | Documentation |
|---------|--------|-------|---------------|
| Theme System | ✅ Complete | ✅ Passing | ✅ Complete |
| Dashboard | ✅ Complete | ✅ Passing | ✅ Complete |
| Filtering | ✅ Complete | ✅ Passing | ✅ Complete |
| Filter Presets | ✅ Complete | ✅ Passing | ✅ Complete |
| Data Export | ✅ Complete | ✅ Passing | ✅ Complete |
| Bookmarks | ✅ Complete | ✅ Passing | ⚠️ Partial |
| Interactive Charts | ✅ Complete | ✅ Passing | ⚠️ Partial |
| Sortable Tables | ✅ Complete | ✅ Passing | ⚠️ Partial |
| Keyboard Shortcuts | ✅ Complete | ✅ Passing | ✅ Complete |
| Responsive Design | ✅ Complete | ✅ Passing | ✅ Complete |
| Accessibility | ✅ Complete | ✅ Passing | ✅ Complete |

## Technology Stack

### Frontend Framework
- **Next.js 16**: App Router, Server Components, ISR
- **React 19**: Functional components, hooks
- **TypeScript**: Strict configuration

### Styling
- **Tailwind CSS**: Utility-first CSS
- **CSS Variables**: Theme tokens
- **shadcn/ui**: Accessible components (Radix primitives)
- **Framer Motion**: Animations

### State Management
- **TanStack Query**: Server state and caching
- **Zustand**: Lightweight client state
- **react-hook-form**: Form state
- **zod**: Validation schemas

### Data Visualization
- **Recharts**: Charts (current)
- **ECharts/D3**: Advanced charts (planned)
- **TanStack Table**: Virtualized tables

### Testing
- **Playwright**: End-to-end tests
- **Vitest**: Unit tests
- **React Testing Library**: Component tests
- **axe-core**: Accessibility tests

## Performance Metrics

### Target Metrics
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

### Optimization Strategies
- Code splitting (route and component-based)
- Lazy loading (images and off-screen components)
- Caching (TanStack Query for server state)
- Virtualization (TanStack Table for large datasets)
- Debouncing (search and filter inputs)
- Image optimization (Next.js Image component)

## Browser Support

### Supported Browsers
- Chrome/Edge: Latest 2 versions
- Firefox: Latest 2 versions
- Safari: Latest 2 versions
- Mobile Safari: iOS 14+
- Chrome Mobile: Android 10+

### Required Features
- JavaScript enabled
- LocalStorage available
- CSS Grid support
- Flexbox support
- CSS Variables support

## Deployment

### Build Commands
```bash
# Install dependencies
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Start production server
npm start

# Run tests
npm test              # Unit tests
npm run test:e2e      # E2E tests
npm run test:a11y     # Accessibility tests
```

### Environment Variables
```bash
NEXT_PUBLIC_API_URL=https://api.utxoiq.com
NEXT_PUBLIC_FIREBASE_API_KEY=...
NEXT_PUBLIC_FIREBASE_AUTH_DOMAIN=...
NEXT_PUBLIC_FIREBASE_PROJECT_ID=...
```

## Maintenance

### Regular Tasks
- **Weekly**: Review accessibility test results
- **Monthly**: Update dependencies
- **Quarterly**: Full accessibility audit
- **Annually**: WCAG compliance review

### Monitoring
- Performance metrics (Core Web Vitals)
- Error tracking (Sentry)
- User analytics (privacy-focused)
- Accessibility issues (automated tests)

## Support

### User Support
- **Documentation**: [frontend/docs/](../frontend/docs/)
- **Community**: [community.utxoiq.com](https://community.utxoiq.com)
- **Email**: support@utxoiq.com
- **Discord**: [discord.gg/utxoiq](https://discord.gg/utxoiq)

### Developer Support
- **API Docs**: [api.utxoiq.com/docs](https://api.utxoiq.com/docs)
- **GitHub**: [github.com/utxoiq](https://github.com/utxoiq)
- **Component Library**: `frontend/src/components/ui/`
- **Design System**: [docs/design.md](./design.md)

## Future Enhancements

### Planned Features
- [ ] Custom theme builder
- [ ] Advanced chart types (ECharts/D3)
- [ ] Collaborative dashboards
- [ ] Real-time collaboration
- [ ] Mobile app (React Native)
- [ ] Offline mode (PWA)
- [ ] Voice commands
- [ ] AI-powered insights

### Under Consideration
- [ ] Widget marketplace
- [ ] Custom widget builder
- [ ] Advanced analytics
- [ ] Integration with external tools
- [ ] White-label options

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0  
**Status**: Production Ready
