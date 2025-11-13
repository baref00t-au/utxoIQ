# Accessibility Documentation

## Overview

utxoIQ is committed to providing an accessible platform for all users, including those with disabilities. This document outlines our accessibility features, implementation guidelines, and testing procedures.

## WCAG 2.1 Level AA Compliance

Our platform conforms to the Web Content Accessibility Guidelines (WCAG) 2.1 at Level AA. This includes:

- **Perceivable**: Information and user interface components must be presentable to users in ways they can perceive
- **Operable**: User interface components and navigation must be operable
- **Understandable**: Information and the operation of user interface must be understandable
- **Robust**: Content must be robust enough to be interpreted by a wide variety of user agents, including assistive technologies

## Accessibility Features

### 1. Keyboard Navigation

All interactive elements are fully accessible via keyboard:

#### Navigation Shortcuts
- **Tab**: Move forward through interactive elements
- **Shift + Tab**: Move backward through interactive elements
- **Enter/Space**: Activate buttons and links
- **Escape**: Close modals and dialogs
- **Arrow Keys**: Navigate within lists and menus

#### Application Shortcuts
- **/**: Focus search input
- **?**: Show keyboard shortcuts help modal
- **↑/↓**: Navigate through insight lists

#### Skip Navigation
- **Skip to Main Content**: First tab stop allows users to bypass navigation and jump directly to main content

### 2. Screen Reader Support

#### Compatible Screen Readers
- **NVDA** (Windows)
- **JAWS** (Windows)
- **VoiceOver** (macOS, iOS)
- **TalkBack** (Android)

#### Implementation Details
- Semantic HTML5 elements (`<header>`, `<nav>`, `<main>`, `<footer>`, `<article>`)
- ARIA landmarks for page regions
- ARIA labels for all icons and icon-only buttons
- Descriptive alt text for all images
- Proper heading hierarchy (h1 → h2 → h3)
- Live regions for dynamic content updates

#### ARIA Attributes Used
```typescript
// Landmarks
role="banner"        // Header
role="navigation"    // Navigation menus
role="main"          // Main content area
role="contentinfo"   // Footer
role="search"        // Search forms

// Widgets
role="dialog"        // Modal dialogs
role="menu"          // Dropdown menus
role="menuitem"      // Menu items
role="status"        // Status messages
role="alert"         // Important alerts

// Properties
aria-label           // Accessible name
aria-labelledby      // Reference to label element
aria-describedby     // Reference to description
aria-hidden="true"   // Hide decorative elements
aria-live            // Live region updates
aria-expanded        // Expandable elements state
aria-selected        // Selected state
```

### 3. Visual Design

#### Color Contrast
All text meets WCAG AA contrast requirements:
- **Normal text**: Minimum 4.5:1 contrast ratio
- **Large text** (18pt+ or 14pt+ bold): Minimum 3:1 contrast ratio
- **Interactive elements**: Minimum 3:1 contrast ratio

#### Theme Support
- **Dark theme** (default): Optimized for low-light environments
- **Light theme**: High contrast for bright environments
- Theme preference persisted in localStorage

#### Focus Indicators
- Visible focus indicators on all interactive elements
- 2px solid brand color ring with 2px offset
- Never removed or hidden with `outline: none` without replacement

#### Text Sizing
- Base font size: 16px
- Responsive typography using `clamp()`
- Text can be resized up to 200% without loss of functionality
- No horizontal scrolling required at 200% zoom

### 4. Mobile Accessibility

#### Touch Targets
- Minimum touch target size: 44×44px
- Adequate spacing between interactive elements
- No overlapping touch targets

#### Responsive Design
- Fully responsive from 320px width
- Mobile-first approach
- Touch-friendly controls
- Gesture alternatives available

#### Reduced Motion
Respects `prefers-reduced-motion` media query:
```css
@media (prefers-reduced-motion: reduce) {
  *,
  *::before,
  *::after {
    animation-duration: 0.01ms !important;
    animation-iteration-count: 1 !important;
    transition-duration: 0.01ms !important;
    scroll-behavior: auto !important;
  }
}
```

## Implementation Guidelines

### Component Accessibility Checklist

When creating new components, ensure:

- [ ] All interactive elements are keyboard accessible
- [ ] Focus indicators are visible
- [ ] ARIA labels provided for icon-only buttons
- [ ] Semantic HTML used where possible
- [ ] Color contrast meets WCAG AA standards
- [ ] Component works with screen readers
- [ ] Touch targets are at least 44×44px
- [ ] Component respects reduced motion preferences

### Code Examples

#### Accessible Button
```typescript
<Button
  onClick={handleClick}
  aria-label="Close dialog"
  className="focus:outline-none focus:ring-2 focus:ring-brand focus:ring-offset-2"
>
  <X className="h-4 w-4" aria-hidden="true" />
</Button>
```

#### Accessible Form Input
```typescript
<div>
  <Label htmlFor="email">Email Address</Label>
  <Input
    id="email"
    type="email"
    aria-required="true"
    aria-invalid={errors.email ? "true" : "false"}
    aria-describedby={errors.email ? "email-error" : undefined}
  />
  {errors.email && (
    <p id="email-error" className="text-sm text-destructive" role="alert">
      {errors.email.message}
    </p>
  )}
</div>
```

#### Accessible Modal
```typescript
<Dialog open={isOpen} onOpenChange={setIsOpen}>
  <DialogContent
    role="dialog"
    aria-labelledby="dialog-title"
    aria-describedby="dialog-description"
  >
    <DialogHeader>
      <DialogTitle id="dialog-title">Confirm Action</DialogTitle>
      <DialogDescription id="dialog-description">
        Are you sure you want to proceed?
      </DialogDescription>
    </DialogHeader>
    {/* Dialog content */}
  </DialogContent>
</Dialog>
```

#### Accessible List
```typescript
<ul role="list" aria-label="Blockchain evidence">
  {evidence.map((item) => (
    <li key={item.id} role="listitem">
      <span className="sr-only">{item.type} identifier:</span>
      {item.type}: {item.id}
    </li>
  ))}
</ul>
```

## Testing Procedures

### Automated Testing

#### Tools Used
- **axe-core**: Automated accessibility testing
- **@axe-core/playwright**: Integration with Playwright tests
- **ESLint plugin**: jsx-a11y for linting

#### Running Tests
```bash
# Run accessibility tests
npm run test:e2e -- tests/accessibility.spec.ts

# Run all tests including accessibility
npm run test:e2e
```

### Manual Testing

#### Keyboard Navigation Testing
1. Disconnect mouse/trackpad
2. Use only keyboard to navigate entire application
3. Verify all interactive elements are reachable
4. Verify focus indicators are visible
5. Verify logical tab order

#### Screen Reader Testing

**NVDA (Windows)**
```bash
# Start NVDA
Ctrl + Alt + N

# Navigate by headings
H / Shift + H

# Navigate by landmarks
D / Shift + D

# Read next item
Down Arrow
```

**VoiceOver (macOS)**
```bash
# Start VoiceOver
Cmd + F5

# Navigate by headings
VO + Cmd + H

# Navigate by landmarks
VO + U, then arrow keys

# Read next item
VO + Right Arrow
```

#### Color Contrast Testing
1. Use browser DevTools to inspect elements
2. Check contrast ratios in Accessibility panel
3. Verify minimum 4.5:1 for normal text
4. Verify minimum 3:1 for large text and UI components

#### Mobile Testing
1. Test on real devices (iOS and Android)
2. Verify touch target sizes
3. Test with screen reader enabled (VoiceOver/TalkBack)
4. Test with zoom enabled (200%)

### Continuous Integration

Accessibility tests run automatically on:
- Every pull request
- Before deployment to production
- Nightly regression tests

## Common Accessibility Patterns

### Loading States
```typescript
<div role="status" aria-live="polite" aria-busy="true">
  <Spinner aria-hidden="true" />
  <span className="sr-only">Loading insights...</span>
</div>
```

### Error Messages
```typescript
<div role="alert" aria-live="assertive">
  <AlertCircle aria-hidden="true" />
  <span>An error occurred. Please try again.</span>
</div>
```

### Dynamic Content Updates
```typescript
// Announce to screen readers
function announceToScreenReader(message: string) {
  const announcement = document.createElement('div');
  announcement.setAttribute('role', 'status');
  announcement.setAttribute('aria-live', 'polite');
  announcement.className = 'sr-only';
  announcement.textContent = message;
  document.body.appendChild(announcement);
  
  setTimeout(() => {
    document.body.removeChild(announcement);
  }, 1000);
}

// Usage
announceToScreenReader('New insight available');
```

### Skip Links
```typescript
<a
  href="#main-content"
  className="sr-only focus:not-sr-only focus:absolute focus:top-4 focus:left-4 focus:z-[100]"
>
  Skip to main content
</a>
```

## Resources

### External Resources
- [WCAG 2.1 Guidelines](https://www.w3.org/WAI/WCAG21/quickref/)
- [ARIA Authoring Practices Guide](https://www.w3.org/WAI/ARIA/apg/)
- [WebAIM Contrast Checker](https://webaim.org/resources/contrastchecker/)
- [axe DevTools](https://www.deque.com/axe/devtools/)

### Internal Resources
- [Accessibility Statement](/accessibility)
- [Keyboard Shortcuts Help Modal](Press `?` in app)
- [Component Library](frontend/src/components/ui/)

## Reporting Issues

If you discover an accessibility issue:

1. **Check existing issues**: Search GitHub issues for similar reports
2. **Create detailed report**: Include:
   - Page/component affected
   - Description of the issue
   - Steps to reproduce
   - Assistive technology used (if applicable)
   - Browser and OS
3. **Label appropriately**: Use `accessibility` label
4. **Priority**: Mark as `high` if it blocks core functionality

## Maintenance

### Regular Reviews
- **Quarterly**: Full accessibility audit
- **Monthly**: Automated test review
- **Weekly**: New component accessibility checks
- **Daily**: CI/CD accessibility tests

### Updates
This documentation is reviewed and updated:
- When new features are added
- When accessibility standards change
- When issues are discovered and resolved
- At least quarterly

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0  
**Maintained By**: utxoIQ Development Team
