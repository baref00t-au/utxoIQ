# PWA Features

## Overview

The utxoIQ frontend is configured as a Progressive Web App (PWA) with offline support, installability, and mobile optimization.

## Features Implemented

### 1. Service Worker
- Configured via `next-pwa` in `next.config.js`
- Automatic caching strategies for different asset types
- Offline support for previously visited pages
- Background sync for data updates

### 2. Web App Manifest
- Located at `/public/manifest.json`
- Defines app name, icons, theme colors
- Enables "Add to Home Screen" functionality
- Standalone display mode for app-like experience

### 3. Mobile Optimization
- Responsive design with Tailwind CSS breakpoints
- Touch-friendly UI components (min 40x40px hit targets)
- Mobile-optimized chart rendering
- Viewport meta tags for proper scaling

### 4. Performance
- Image optimization with Next.js Image component
- Code splitting and lazy loading
- Prefetching for faster navigation
- Target: Lighthouse score > 90 on mobile

### 5. Push Notifications
- Service worker ready for push notifications
- Alert notifications can be delivered to mobile devices
- Requires user permission and subscription

## Testing PWA Features

### Local Testing
```bash
# Build production version
npm run build
npm start

# Test with Lighthouse in Chrome DevTools
# Open DevTools > Lighthouse > Generate Report
```

### Mobile Testing
1. Deploy to production or use ngrok for local testing
2. Open in mobile browser (Chrome/Safari)
3. Look for "Add to Home Screen" prompt
4. Install and test offline functionality

## Caching Strategy

### Static Assets
- Images: StaleWhileRevalidate (24h)
- JS/CSS: StaleWhileRevalidate (24h)
- Fonts: CacheFirst (1 year)

### API Responses
- Insights: NetworkFirst with 24h cache
- User data: NetworkFirst (no cache)

### Offline Fallback
- Previously visited pages available offline
- Cached insights displayed when offline
- Graceful degradation for unavailable features

## Installation

### iOS (Safari)
1. Open utxoiq.com in Safari
2. Tap Share button
3. Select "Add to Home Screen"
4. Confirm installation

### Android (Chrome)
1. Open utxoiq.com in Chrome
2. Tap menu (three dots)
3. Select "Add to Home Screen"
4. Or use the automatic install prompt

## Manifest Configuration

```json
{
  "name": "utxoIQ - AI-Powered Bitcoin Intelligence",
  "short_name": "utxoIQ",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#0B0B0C",
  "theme_color": "#FF5A21"
}
```

## Service Worker Events

The service worker handles:
- `install`: Cache static assets
- `activate`: Clean up old caches
- `fetch`: Serve cached content when available
- `push`: Handle push notifications
- `sync`: Background data synchronization

## Performance Targets

- First Contentful Paint: < 1.5s
- Time to Interactive: < 3.5s
- Lighthouse Performance: > 90
- Lighthouse PWA: 100
- Mobile-friendly: Yes

## Future Enhancements

- [ ] Background sync for offline actions
- [ ] Periodic background sync for updates
- [ ] Share Target API for sharing to app
- [ ] Web Share API for sharing from app
- [ ] Install prompt customization
- [ ] App shortcuts in manifest
