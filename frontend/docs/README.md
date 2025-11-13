# utxoIQ Frontend Documentation

## Overview

Welcome to the utxoIQ frontend documentation. This directory contains comprehensive guides for using and customizing the utxoIQ platform's user interface and user experience features.

## Documentation Index

### User Guides

#### [Accessibility Guide](./ACCESSIBILITY.md)
Complete guide to accessibility features, WCAG 2.1 AA compliance, keyboard navigation, screen reader support, and testing procedures.

**Topics covered**:
- Keyboard navigation shortcuts
- Screen reader compatibility (NVDA, JAWS, VoiceOver, TalkBack)
- Color contrast requirements
- Focus indicators and visual design
- Mobile accessibility
- Testing procedures and tools

#### [Theme Customization](./THEME_CUSTOMIZATION.md)
Learn how to use and customize the theme system, including dark/light themes, CSS variables, and creating custom color schemes.

**Topics covered**:
- Theme provider usage
- CSS variables and color tokens
- Tailwind configuration
- Adding new themes
- Chart theming
- Accessibility considerations

#### [Dashboard Customization](./DASHBOARD_CUSTOMIZATION.md)
Master the drag-and-drop dashboard system, widget management, and layout persistence.

**Topics covered**:
- Drag-and-drop layout
- Widget resizing and configuration
- Widget library
- Layout management (save, export, import)
- Grid system and responsive behavior
- Keyboard shortcuts for dashboard

#### [Filter Presets](./FILTER_PRESETS.md)
Save and manage filter combinations for quick access to your most-used searches.

**Topics covered**:
- Creating and using presets
- Managing presets (edit, delete, reorder)
- Preset limits by tier
- Advanced features (sharing, export/import)
- Common preset examples
- API integration

#### [Data Export](./DATA_EXPORT.md)
Export blockchain insights and data in CSV and JSON formats for external analysis.

**Topics covered**:
- Supported formats (CSV, JSON)
- Export limits by tier
- Column definitions and structure
- Batch export and scheduled exports
- API export for automation
- Usage examples (Excel, Python, R)

#### [Keyboard Shortcuts](./KEYBOARD_SHORTCUTS.md)
Complete reference of all keyboard shortcuts for efficient navigation and interaction.

**Topics covered**:
- Global shortcuts
- Navigation shortcuts
- Feature-specific shortcuts (insights, dashboard, charts)
- Accessibility shortcuts
- Customizing shortcuts
- Platform-specific differences

### Technical Documentation

#### [PWA Guide](./PWA.md)
Progressive Web App features, offline support, and installation instructions.

## Quick Start

### For End Users

1. **Getting Started**
   - Sign up at [utxoiq.com](https://utxoiq.com)
   - Review [Accessibility Guide](./ACCESSIBILITY.md) for navigation tips
   - Press **?** anywhere to see [Keyboard Shortcuts](./KEYBOARD_SHORTCUTS.md)

2. **Customize Your Experience**
   - Toggle theme with **Ctrl/Cmd + /** or use theme toggle in header
   - Arrange your [Dashboard](./DASHBOARD_CUSTOMIZATION.md) with drag-and-drop
   - Create [Filter Presets](./FILTER_PRESETS.md) for common searches

3. **Export and Analyze**
   - [Export data](./DATA_EXPORT.md) in CSV or JSON format
   - Use in Excel, Python, R, or other analysis tools
   - Set up scheduled exports (Power tier)

### For Developers

1. **Architecture**
   - Next.js 16 with App Router
   - TypeScript with strict configuration
   - Tailwind CSS with CSS variables
   - shadcn/ui components (Radix primitives)

2. **Key Technologies**
   - **State Management**: TanStack Query (server), Zustand (client)
   - **Forms**: react-hook-form + zod
   - **Charts**: Recharts (migrating to ECharts/D3)
   - **Tables**: TanStack Table with virtualization
   - **Animation**: Framer Motion
   - **Testing**: Playwright (e2e) + Vitest (unit)

3. **Development Setup**
   ```bash
   # Install dependencies
   npm install
   
   # Start development server
   npm run dev
   
   # Run tests
   npm test              # Unit tests
   npm run test:e2e      # E2E tests
   
   # Build for production
   npm run build
   ```

## Feature Overview

### Theme System
- **Dark theme** (default) and **light theme**
- CSS variables for all colors
- Automatic persistence in localStorage
- System preference detection
- Smooth transitions between themes

### Dashboard
- **Drag-and-drop** widget arrangement
- **Resizable widgets** with grid constraints
- **Widget library** with 8+ widget types
- **Auto-save** layout changes
- **Export/import** layouts
- **Responsive** design (mobile, tablet, desktop)

### Filtering
- **Full-text search** with debouncing
- **Category filters** (Mempool, Exchange, Miner, Whale)
- **Confidence threshold** slider
- **Date range** picker
- **Filter presets** (save up to 10)
- **URL persistence** of filter state

### Data Export
- **CSV format** for Excel/Sheets
- **JSON format** for programming
- **Batch export** multiple filters
- **Scheduled exports** (Power tier)
- **API access** for automation
- **Export limits** by subscription tier

### Keyboard Navigation
- **50+ shortcuts** for common actions
- **Fully keyboard accessible**
- **Screen reader compatible**
- **Customizable shortcuts** (Power tier)
- **Help modal** (press **?**)

### Accessibility
- **WCAG 2.1 AA compliant**
- **Keyboard navigation** for all features
- **Screen reader support** (NVDA, JAWS, VoiceOver)
- **Color contrast** 4.5:1 minimum
- **Focus indicators** on all interactive elements
- **Touch targets** 44×44px minimum

## Subscription Tiers

### Free Tier
- Basic insight access
- 3 filter presets
- 100 rows per export
- CSV export only
- Dark/light themes

### Pro Tier
- Enhanced alerts
- 10 filter presets
- 1,000 rows per export
- CSV and JSON export
- Batch export
- Extended API access

### Power Tier
- Unlimited chat queries
- Unlimited filter presets
- 10,000 rows per export
- Scheduled exports
- Shared presets
- Custom shortcuts
- Team features

## Browser Support

### Supported Browsers
- **Chrome/Edge**: Latest 2 versions
- **Firefox**: Latest 2 versions
- **Safari**: Latest 2 versions
- **Mobile Safari**: iOS 14+
- **Chrome Mobile**: Android 10+

### Required Features
- JavaScript enabled
- LocalStorage available
- CSS Grid support
- Flexbox support
- CSS Variables support

## Accessibility Standards

### WCAG 2.1 Level AA Compliance

The platform meets all Level AA success criteria:

#### Perceivable
- Text alternatives for non-text content
- Captions and alternatives for multimedia
- Adaptable content structure
- Distinguishable visual presentation

#### Operable
- Keyboard accessible functionality
- Sufficient time for interactions
- Seizure-safe design (no flashing)
- Navigable and findable content

#### Understandable
- Readable and understandable text
- Predictable functionality
- Input assistance and error prevention

#### Robust
- Compatible with assistive technologies
- Valid HTML and ARIA markup

## Performance

### Optimization Strategies
- **Code splitting**: Route-based and component-based
- **Lazy loading**: Images and off-screen components
- **Caching**: TanStack Query for server state
- **Virtualization**: TanStack Table for large datasets
- **Debouncing**: Search and filter inputs
- **Image optimization**: Next.js Image component

### Performance Targets
- **First Contentful Paint**: < 1.5s
- **Time to Interactive**: < 3.5s
- **Largest Contentful Paint**: < 2.5s
- **Cumulative Layout Shift**: < 0.1
- **First Input Delay**: < 100ms

## Security

### Client-Side Security
- **XSS Prevention**: React automatic escaping
- **CSRF Protection**: Token-based authentication
- **Content Security Policy**: Strict CSP headers
- **Secure Storage**: Encrypted localStorage for sensitive data
- **HTTPS Only**: All connections encrypted

### Authentication
- **Firebase Auth**: Industry-standard authentication
- **JWT Tokens**: Secure token-based sessions
- **Token Refresh**: Automatic token renewal
- **Session Management**: Secure session handling

## Contributing

### Reporting Issues
1. Check existing issues on GitHub
2. Create detailed bug report with:
   - Steps to reproduce
   - Expected vs actual behavior
   - Browser and OS information
   - Screenshots if applicable

### Suggesting Features
1. Search existing feature requests
2. Create detailed feature proposal with:
   - Use case description
   - Expected behavior
   - Mockups or examples
   - Priority and impact

### Documentation Improvements
1. Fork repository
2. Make documentation changes
3. Submit pull request
4. Include reason for changes

## Resources

### External Resources
- [Next.js Documentation](https://nextjs.org/docs)
- [React Documentation](https://react.dev)
- [Tailwind CSS](https://tailwindcss.com)
- [shadcn/ui](https://ui.shadcn.com)
- [WCAG Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)

### Internal Resources
- [API Documentation](https://api.utxoiq.com/docs)
- [Component Library](../src/components/ui/)
- [Design System](../../docs/design.md)
- [Architecture Guide](../../docs/structure.md)

### Community
- **Website**: [utxoiq.com](https://utxoiq.com)
- **Documentation**: [docs.utxoiq.com](https://docs.utxoiq.com)
- **Community**: [community.utxoiq.com](https://community.utxoiq.com)
- **Discord**: [discord.gg/utxoiq](https://discord.gg/utxoiq)
- **GitHub**: [github.com/utxoiq](https://github.com/utxoiq)

## Support

### Getting Help
- **Documentation**: Start here for most questions
- **Community Forum**: Ask questions and share tips
- **Discord**: Real-time chat with community
- **Email Support**: support@utxoiq.com
- **GitHub Issues**: Bug reports and feature requests

### Support Hours
- **Community**: 24/7 via Discord and forum
- **Email Support**: Business hours (9 AM - 5 PM UTC)
- **Priority Support**: Power tier subscribers

## Changelog

### Version 1.0.0 (November 12, 2025)

#### Features
- ✅ Theme system (dark/light)
- ✅ Drag-and-drop dashboard
- ✅ Advanced filtering with presets
- ✅ Data export (CSV/JSON)
- ✅ Bookmark system
- ✅ Interactive charts
- ✅ Sortable tables
- ✅ Keyboard shortcuts
- ✅ Responsive design
- ✅ WCAG 2.1 AA accessibility

#### Documentation
- ✅ Accessibility guide
- ✅ Theme customization guide
- ✅ Dashboard customization guide
- ✅ Filter presets guide
- ✅ Data export guide
- ✅ Keyboard shortcuts reference

## License

Copyright © 2025 utxoIQ. All rights reserved.

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0  
**Maintained By**: utxoIQ Development Team
