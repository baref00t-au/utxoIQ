# Theme Customization Guide

## Overview

utxoIQ supports both dark and light themes with a comprehensive theming system built on CSS variables and Tailwind CSS. This guide explains how to customize themes, add new color schemes, and maintain consistent styling across the application.

## Theme System Architecture

### Theme Provider

The theme system is managed by a React Context provider located in `src/lib/theme.tsx`:

```typescript
import { useTheme } from '@/lib/theme';

function MyComponent() {
  const { theme, toggleTheme, setTheme } = useTheme();
  
  return (
    <button onClick={toggleTheme}>
      Current theme: {theme}
    </button>
  );
}
```

### Theme Persistence

- Theme preference is automatically saved to `localStorage`
- On first visit, the system detects the user's OS preference via `prefers-color-scheme`
- Theme persists across sessions and page reloads

## Using the Theme System

### Toggle Theme

```typescript
import { useTheme } from '@/lib/theme';

export function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <Button onClick={toggleTheme} aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}>
      {theme === 'dark' ? <Sun /> : <Moon />}
    </Button>
  );
}
```

### Set Specific Theme

```typescript
const { setTheme } = useTheme();

// Set to dark theme
setTheme('dark');

// Set to light theme
setTheme('light');
```

### Get Current Theme

```typescript
const { theme } = useTheme();

if (theme === 'dark') {
  // Dark theme specific logic
}
```

## CSS Variables

### Color Tokens

All colors are defined as CSS variables in `src/app/globals.css`:

#### Dark Theme (Default)
```css
:root[data-theme="dark"] {
  --background: #0B0B0C;        /* Main background */
  --surface: #131316;           /* Card/panel backgrounds */
  --border: #2A2A2E;            /* Border color */
  --text-primary: #F4F4F5;      /* Primary text */
  --text-secondary: #A1A1AA;    /* Secondary text */
  --brand: #FF5A21;             /* Brand orange */
  --success: #16A34A;           /* Success green */
  --warning: #D97706;           /* Warning amber */
  --error: #DC2626;             /* Error red */
}
```

#### Light Theme
```css
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

### Using CSS Variables

#### In CSS/Tailwind
```css
.my-component {
  background-color: var(--surface);
  color: var(--text-primary);
  border: 1px solid var(--border);
}
```

#### In Tailwind Classes
```tsx
<div className="bg-background text-text-primary border-border">
  Content
</div>
```

## Tailwind Configuration

### Color Tokens

The `tailwind.config.js` maps CSS variables to Tailwind utilities:

```javascript
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
        success: 'var(--success)',
        warning: 'var(--warning)',
        error: 'var(--error)',
      },
    },
  },
};
```

### Usage Examples

```tsx
// Background colors
<div className="bg-background">...</div>
<div className="bg-surface">...</div>

// Text colors
<p className="text-text-primary">Primary text</p>
<p className="text-text-secondary">Secondary text</p>

// Brand colors
<button className="bg-brand text-white">Action</button>
<div className="border-brand">...</div>

// Status colors
<span className="text-success">Success message</span>
<span className="text-warning">Warning message</span>
<span className="text-error">Error message</span>
```

## Adding a New Theme

### Step 1: Define CSS Variables

Add a new theme variant in `globals.css`:

```css
:root[data-theme="custom"] {
  --background: #your-color;
  --surface: #your-color;
  --border: #your-color;
  --text-primary: #your-color;
  --text-secondary: #your-color;
  --brand: #your-color;
  --success: #your-color;
  --warning: #your-color;
  --error: #your-color;
}
```

### Step 2: Update Theme Type

Modify `src/lib/theme.tsx`:

```typescript
type Theme = 'light' | 'dark' | 'custom';
```

### Step 3: Add Theme Selector

```typescript
export function ThemeSelector() {
  const { theme, setTheme } = useTheme();
  
  return (
    <Select value={theme} onValueChange={setTheme}>
      <SelectTrigger>
        <SelectValue />
      </SelectTrigger>
      <SelectContent>
        <SelectItem value="light">Light</SelectItem>
        <SelectItem value="dark">Dark</SelectItem>
        <SelectItem value="custom">Custom</SelectItem>
      </SelectContent>
    </Select>
  );
}
```

## Category Colors

Category-specific colors for insights:

```css
:root {
  --category-mempool: #FB923C;   /* Orange */
  --category-exchange: #38BDF8;  /* Sky blue */
  --category-miner: #10B981;     /* Emerald */
  --category-whale: #8B5CF6;     /* Violet */
}
```

Usage:
```tsx
<Badge className="bg-[var(--category-mempool)]">Mempool</Badge>
```

## Component Theming

### shadcn/ui Components

All shadcn/ui components automatically support theming through CSS variables. No additional configuration needed.

```tsx
import { Button } from '@/components/ui/button';

// Automatically themed
<Button>Click me</Button>
```

### Custom Components

When creating custom components, use CSS variables:

```tsx
export function CustomCard({ children }: { children: React.ReactNode }) {
  return (
    <div className="rounded-lg border border-border bg-surface p-4">
      {children}
    </div>
  );
}
```

## Chart Theming

### Recharts

Charts automatically use theme colors:

```tsx
import { LineChart, Line } from 'recharts';

<LineChart data={data}>
  <Line 
    type="monotone" 
    dataKey="value" 
    stroke="var(--brand)" 
  />
</LineChart>
```

### Chart Exports

Exported charts include current theme colors:

```typescript
import { exportChartToPNG } from '@/lib/chart-export';

// Exports with current theme applied
await exportChartToPNG(chartElement, 'chart.png');
```

## Accessibility Considerations

### Color Contrast

All theme colors meet WCAG 2.1 AA contrast requirements:
- Normal text: 4.5:1 minimum
- Large text: 3:1 minimum
- UI components: 3:1 minimum

### Testing Contrast

Use browser DevTools to verify contrast ratios:
1. Inspect element
2. Open Accessibility panel
3. Check contrast ratio

### Focus Indicators

Focus indicators use brand color with proper contrast:

```css
.focus-visible {
  outline: 2px solid var(--brand);
  outline-offset: 2px;
}
```

## Reduced Motion

The theme system respects user motion preferences:

```css
@media (prefers-reduced-motion: reduce) {
  * {
    animation-duration: 0.01ms !important;
    transition-duration: 0.01ms !important;
  }
}
```

## Best Practices

### Do's
✅ Use CSS variables for all colors  
✅ Test both themes when adding new components  
✅ Verify color contrast ratios  
✅ Use semantic color names (background, surface, border)  
✅ Provide theme toggle in accessible location  

### Don'ts
❌ Don't hardcode color values  
❌ Don't assume dark theme only  
❌ Don't use colors that fail contrast checks  
❌ Don't override theme colors without good reason  
❌ Don't forget to test theme switching  

## Troubleshooting

### Theme Not Persisting

Check localStorage:
```javascript
localStorage.getItem('theme'); // Should return 'dark' or 'light'
```

Clear and reset:
```javascript
localStorage.removeItem('theme');
window.location.reload();
```

### Colors Not Updating

Ensure CSS variables are defined:
```javascript
getComputedStyle(document.documentElement)
  .getPropertyValue('--background');
```

### Theme Flashing on Load

The theme provider includes a mounted state to prevent flash:
```typescript
const [mounted, setMounted] = useState(false);

useEffect(() => {
  setMounted(true);
}, []);
```

## Examples

### Complete Theme-Aware Component

```tsx
'use client';

import { useTheme } from '@/lib/theme';
import { Moon, Sun } from 'lucide-react';
import { Button } from '@/components/ui/button';

export function ThemedComponent() {
  const { theme, toggleTheme } = useTheme();
  
  return (
    <div className="rounded-lg border border-border bg-surface p-6">
      <h2 className="text-xl font-semibold text-text-primary mb-4">
        Theme Settings
      </h2>
      <p className="text-text-secondary mb-4">
        Current theme: {theme}
      </p>
      <Button 
        onClick={toggleTheme}
        className="bg-brand hover:bg-brand/90"
        aria-label={`Switch to ${theme === 'dark' ? 'light' : 'dark'} theme`}
      >
        {theme === 'dark' ? (
          <>
            <Sun className="mr-2 h-4 w-4" />
            Switch to Light
          </>
        ) : (
          <>
            <Moon className="mr-2 h-4 w-4" />
            Switch to Dark
          </>
        )}
      </Button>
    </div>
  );
}
```

## Resources

- [CSS Variables Documentation](https://developer.mozilla.org/en-US/docs/Web/CSS/Using_CSS_custom_properties)
- [Tailwind CSS Theming](https://tailwindcss.com/docs/theme)
- [WCAG Color Contrast](https://www.w3.org/WAI/WCAG21/Understanding/contrast-minimum.html)
- [prefers-color-scheme](https://developer.mozilla.org/en-US/docs/Web/CSS/@media/prefers-color-scheme)

---

**Last Updated**: November 12, 2025  
**Version**: 1.0.0
