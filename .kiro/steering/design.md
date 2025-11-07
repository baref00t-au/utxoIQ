# Design System & UI Guidelines

## Brand & Design System

### Tone
Factual, calm, minimalist

### Color Palette (Dark-first)

#### Base Colors
- **Background**: `#0B0B0C` (zinc-950)
- **Surface**: `#131316` (zinc-900)
- **Border**: `#2A2A2E` (zinc-800)
- **Text Primary**: `#F4F4F5` (zinc-50)
- **Text Secondary**: `#A1A1AA` (zinc-400)

#### Accent & Status
- **Brand/Accent**: `#FF5A21` (electric orange)
- **Success**: `#16A34A`
- **Warning**: `#D97706`

#### Category Colors
- **Mempool**: `#FB923C` (orange)
- **Exchange**: `#38BDF8` (sky)
- **Miner**: `#10B981` (emerald)
- **Whale**: `#8B5CF6` (violet)

### Typography

#### Font Families
- **Primary**: System or Inter
- **Monospace**: JetBrains Mono / Menlo (for numbers, txids, addresses)

#### Type Scale
- **Display**: 44px/52px, semibold
- **H1**: 32px/40px, semibold
- **H2**: 24px/32px, semibold
- **H3**: 18px/28px, medium
- **Body**: 16px/24px, regular
- **Caption**: 13px/20px, regular

#### Responsive Typography
Mobile: reduce one step (H1→H2, H3→Body Bold)

### Spacing Scale
Base: 4px (4, 8, 12, 16, 24, 32, 48, 64)

### Border Radius
- **Cards/Inputs**: 16px
- **Hero**: 24px
- **Pills/Badges**: 8px

### Elevation
- **Default**: shadow-sm
- **Hover/Focus**: shadow-md
- Avoid heavy shadows; use soft shadows only

### Grid System
- **Desktop**: 12 columns
- **Tablet**: 4 columns
- **Mobile**: Single column
- **Max content width**: 1280px / 1440px

### Breakpoints
- **Mobile**: ≤ 639px
- **Tablet**: 640–1023px
- **Desktop**: ≥ 1024px

### Iconography
- **Style**: lucide-style line icons
- **Stroke**: 1.5px
- **Size**: 20–24px

### Charts
- Minimal grid
- 1px axis lines
- No bright fills
- Use brand orange for emphasis only
- Height: 160–220px (inline), 140px min (mobile)
- Aspect ratio: 16:9 or 16:6

### Interactions
- **Animation duration**: 150–200ms
- **Easing**: ease-out
- **Focus rings**: 2px brand orange at 50% opacity

## Information Architecture

### Top-level Pages
- **Feed** (`/`) - Real-time insights list (default landing after auth)
- **Brief** (`/brief`) - Daily 07:00 UTC roundup
- **Insight** (`/insight/{id}`) - Detail page per insight
- **Alerts** (`/alerts`) - Create/manage smart alerts
- **Pricing** (`/pricing`) - Free / Pro / Power tiers
- **Auth** (`/sign-in`, `/sign-up`) - Authentication pages

### Global Elements
- Header (64px height)
- Left rail (256px, filters)
- Content area
- Footer

## Global Layout

### Header (64px height)
- **Left**: Brand icon (cube+spark) + "utxoIQ"
- **Center** (Desktop): Nav links — Feed, Brief, Ask (P2)
- **Right**: GitHub (outline button), Sign in (brand button)
- **Style**: Translucent dark background, 1px bottom border
- **Active state**: 2px underline in brand color
- **Hover**: Subtle background tint

### Page Grid
- **Desktop**: Left rail 256px + content 1fr (24px gap)
- **Tablet**: Left rail collapses into accordions above content
- **Mobile**: Single column; filters in sheet/drawer

### Footer
- **Left**: © year + tagline
- **Right**: Privacy, Terms links

## Component Specifications

### Insight Card
- **Container**: 16px radius, 1px border (#2A2A2E), dark surface
- **Header Row**: Colored dot (category), UPPERCASE category label, timestamp (hh:mm)
- **Title**: H3 (18/28), max 2 lines, truncation ellipsis
- **Summary**: Body (16/24), max 3 lines on feed
- **Confidence Badge**: Right-aligned pill
  - ≥85% green
  - 70–84% amber
  - <70% neutral
- **Chart**: Inline sparkline (160–220px height) or PNG from GCS (16:6)
- **Evidence chips**: Block/txid counts; monospaced if showing IDs
- **Actions**: Share (icon button), "View detail" (primary button)
- **Loading state**: Skeleton (title line, 2 body lines, chart shimmer)

### Daily Brief Card
- **Header**: Lightning icon + "07:00 UTC"
- **Content**: List of top 3 events (headline + 1-line summary)
- **Buttons**: "Preview public brief" (secondary), "Post to X" (primary)

### Filters Panel (Left Rail)
- Search input + icon button
- Tabs: All / Mempool / Exchange / Miner / Whale
- Toggle: "High confidence only (≥0.7)"
- Time range (future): last 1h / 4h / 24h

### Smart Alert Form
- **Fields**: Metric (select), Threshold (input), Channel (select), Confidence toggle, Note (textarea)
- **Primary button**: "Create alert"
- **Validation**: Clear helper text under inputs

### Badges & Dots
- 12px dot + label
- Badges use outline on dark surfaces

### Empty / Loading / Error States
- **Empty Feed**: Icon + "No insights yet" + CTA to set alerts
- **Loading**: Skeletons for 3–5 cards
- **Error**: Toast + retry button on panel

## Page Layouts

### Feed (Home)
```
┌─────────────────────────────────────────────────────────────── Header ─────┐
│ utxoIQ      Feed  Brief  Ask                               GitHub  Sign in │
└─────────────────────────────────────────────────────────────────────────────┘
┌ Left Rail (256px) ┐  ┌──────────── Content (1fr) ───────────┐
│ Search [    ] ⌕    │  [ Insight Card ]                       │
│ Tabs: All/M/E/M/W  │  [ Insight Card ]                       │
│ Confidence ≥0.7 ⎘  │  [ Insight Card ]                       │
└────────────────────┘  └──────────────────────────────────────┘
────────────────────────────────────────────────────────────── Footer ───────
```
- **Content**: 8–12 cards paginated/infinite-scroll (virtualized list optional)
- **Acceptance**: Cards truncate correctly, chart renders 160–220px, confidence badge visible

### Insight Detail (`/insight/{id}`)
```
Title (H1 32/40)
meta: • Mempool  |  09:18  |  Confidence 82%
[ Hero Chart 16:9 ]
Summary paragraph
Evidence table (blocks/txids)
Share: [X] [Copy Link]
Related insights (3-up)
```
- **Hero chart**: PNG 1200×630, 16:9 or 16:6 responsive
- **Evidence table**: Monospace font, copy-to-clipboard buttons
- **OG tags**: Generate preview with title, description, chart image

### Daily Brief (`/brief`)
- H1 + date/time "Daily Brief — 07:00 UTC"
- Cards list (top 3–5)
- Public preview banner (shareable)
- CTA: Follow on X

### Alerts (`/alerts`)
- **Layout**: Form (left) + My Alerts list (right)
- **List items**: Metric, threshold, channel, status toggle, last triggered
- **Empty state**: Illustration

### Pricing (`/pricing`)
- 3 cards (Free / Pro / Power)
- Highlight Power with brand accent border
- Feature list checkmarks
- CTA connects to Stripe

### Auth (`/sign-in`, `/sign-up`)
- Centered card
- Brand icon
- Social/email options
- Legal text (terms/privacy)

## Responsive Rules

### Mobile (≤ 639px)
- Header collapses to hamburger
- Left rail becomes bottom sheet
- Card paddings: 24px → 16px
- Title sizes drop one step (H1→H2, H3→Body Bold)
- Charts min-height: 140px
- Hide evidence chips if < 360px

### Tablet (640–1023px)
- Two-column content allowed for related insights
- Left rail collapses into accordions above content

## Accessibility & UX

### Requirements
- Keyboard focus visible on all interactive elements
- Color contrast ≥ 4.5:1 for text on dark
- Hit targets ≥ 40×40px
- Live regions for toasts (ARIA role=alert)
- Time values include title attribute with ISO string

## Motion & Animation

### Card Hover
- Elevate from shadow-sm → shadow-md
- translateY(-1px)

### Tab/Filter Changes
- 150ms fade + slide (4px)

### Chart Mount
- Fade-in 200ms (no distracting sweeps)

## Asset Guidelines

### Chart PNGs
- 2× pixel density for crispness
- Color-safe on dark background
- 1200×630 for OG images

### OG Images
- 1200×630
- Include headline + tiny category dot

### Icons
- 20–24px
- Consistent stroke (1.5px)

## Component Inventory

### Atoms
Button, Input, Select, Badge, Tabs, Switch, Tooltip, Separator, Progress

### Molecules
InsightCard, DailyBriefCard, AlertForm, EvidenceTable, PricingTierCard

### Organisms
FeedList, FiltersPanel, Header, Footer, InsightDetail

## TypeScript Component Props

### InsightCard
```typescript
interface InsightCardProps {
  id: string;
  category: 'mempool' | 'exchange' | 'miner' | 'whale';
  headline: string;
  summary: string;
  confidence: number;
  createdAt: string; // ISO string
  chartUrl?: string;
  evidence?: {
    blocks?: number[];
    txids?: string[];
  };
}
```

### PricingTierCard
```typescript
interface PricingTierCardProps {
  name: 'Free' | 'Pro' | 'Power';
  price: string;
  features: string[];
  ctaText: string;
  highlight?: boolean;
}
```

## Implementation Notes

### Tailwind Configuration
- Define CSS variables for all color tokens
- Use `clamp()` for responsive typography
- Dark mode first, light mode via CSS variables (future)

### Next.js Patterns
- Server Components for static content
- Client Components for interactive elements
- ISR for insight detail pages
- Streaming with Suspense for Live Feed

### shadcn/ui Integration
- Theme all components to brand colors
- Use Radix primitives for accessibility
- Customize with CSS variables

## Handoff Checklist

- [ ] Header responsive & sticky with border
- [ ] Feed page matches spacing/typography scale
- [ ] Insight card truncation, states (loading/empty/error)
- [ ] Detail page OG tags & copy-to-clipboard on evidence
- [ ] Daily Brief page with top-3 items
- [ ] Alerts page form validation & list view
- [ ] Pricing page with three tiers and CTA hooks
- [ ] Accessibility checks pass (contrast, focus, keyboard)
