# utxoIQ Frontend

Next.js 16 PWA frontend for the utxoIQ Bitcoin intelligence platform.

## Features

- **Next.js 16** with App Router and Server Components
- **TypeScript** for type safety
- **Tailwind CSS** with custom design system
- **Firebase Auth** for user authentication
- **PWA Support** with offline capabilities
- **WebSocket** for real-time insight streaming
- **shadcn/ui** components with Radix primitives
- **TanStack Query** for server state management
- **Zustand** for client state management

## Getting Started

### Prerequisites

- Node.js 18+ 
- npm or yarn

### Installation

```bash
# Install dependencies
npm install

# Copy environment variables
cp .env.example .env.local

# Update .env.local with your Firebase credentials
```

### Development

```bash
# Start development server
npm run dev

# Open http://localhost:3000
```

### Build

```bash
# Build for production
npm run build

# Start production server
npm start
```

### Testing

```bash
# Run unit tests
npm test

# Run e2e tests
npm run test:e2e

# Type checking
npm run type-check
```

## Project Structure

```
src/
├── app/                    # Next.js app router pages
├── components/             # React components
│   ├── ui/                # Base UI components (shadcn/ui)
│   ├── layout/            # Layout components
│   ├── insights/          # Insight-related components
│   ├── alerts/            # Alert management
│   ├── chat/              # AI chat interface
│   └── billing/           # Subscription management
├── lib/                   # Utilities and configurations
│   ├── firebase.ts        # Firebase configuration
│   ├── auth-context.tsx   # Auth context provider
│   ├── websocket.ts       # WebSocket hook
│   └── utils.ts           # Utility functions
└── types/                 # TypeScript type definitions
```

## Environment Variables

See `.env.example` for required environment variables.

## PWA Features

- Offline support with service worker
- Installable on mobile devices
- Push notifications for alerts
- Optimized caching strategies

## Authentication

Firebase Auth is used for user authentication with support for:
- Email/password authentication
- Google OAuth
- Protected routes

## Real-time Updates

WebSocket connection provides real-time streaming of:
- New insights
- Mempool updates
- Alert notifications

## Deployment

```bash
# Build Docker image
docker build -t utxoiq-frontend .

# Deploy to Cloud Run
gcloud run deploy utxoiq-frontend --source .
```
