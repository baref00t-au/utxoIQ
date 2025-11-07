# utxoIQ JavaScript/TypeScript SDK

Official JavaScript/TypeScript SDK for the utxoIQ Bitcoin blockchain intelligence platform.

## Installation

```bash
npm install @utxoiq/sdk
# or
yarn add @utxoiq/sdk
# or
pnpm add @utxoiq/sdk
```

## Quick Start

### Authentication with Firebase Auth

```typescript
import { UtxoIQClient } from '@utxoiq/sdk';

// Initialize with Firebase Auth token
const client = new UtxoIQClient({
  firebaseToken: 'your-firebase-jwt-token'
});

// Get latest insights
const insights = await client.insights.getLatest({ limit: 10 });
insights.forEach(insight => {
  console.log(`${insight.headline} (confidence: ${insight.confidence})`);
});
```

### Authentication with API Key

```typescript
import { UtxoIQClient } from '@utxoiq/sdk';

// Initialize with API key
const client = new UtxoIQClient({
  apiKey: 'your-api-key'
});

// Get specific insight
const insight = await client.insights.getById('insight-id-123');
console.log(insight.summary);
```

## Features

- **Full TypeScript support** with comprehensive type definitions
- **Automatic retry logic** with exponential backoff
- **Firebase Auth and API key support**
- **Promise-based API** with async/await
- **Comprehensive error handling**
- **Tree-shakeable** ESM and CommonJS builds

## Usage Examples

### Get Latest Insights

```typescript
// Get latest insights with filtering
const insights = await client.insights.getLatest({
  limit: 20,
  category: 'mempool',
  minConfidence: 0.7
});
```

### Access Daily Brief

```typescript
// Get daily brief for specific date
const brief = await client.dailyBrief.getByDate(new Date('2025-11-07'));
console.log(`Top events: ${brief.insights.length}`);

// Get latest daily brief
const latestBrief = await client.dailyBrief.getLatest();
```

### Manage Alerts

```typescript
// Create a new alert
const alert = await client.alerts.create({
  signalType: 'mempool',
  threshold: 100.0,
  operator: 'gt',
  notificationChannel: 'email'
});

// List user alerts
const alerts = await client.alerts.list();

// Update alert
await client.alerts.update(alert.id, { isActive: false });

// Delete alert
await client.alerts.delete(alert.id);
```

### Submit Feedback

```typescript
// Rate an insight
await client.feedback.submit({
  insightId: 'insight-123',
  rating: 'useful',
  comment: 'Very helpful analysis'
});

// Get accuracy leaderboard
const leaderboard = await client.feedback.getAccuracyLeaderboard();
```

### AI Chat Queries

```typescript
// Ask natural language questions
const response = await client.chat.query({
  question: 'What are the current mempool fee rates?'
});
console.log(response.answer);
```

### Guest Mode (Public Access)

```typescript
// Access public insights without authentication
const client = new UtxoIQClient(); // No auth required
const publicInsights = await client.insights.getPublic({ limit: 20 });
```

## Error Handling

```typescript
import {
  UtxoIQError,
  AuthenticationError,
  RateLimitError,
  ValidationError
} from '@utxoiq/sdk';

try {
  const insights = await client.insights.getLatest();
} catch (error) {
  if (error instanceof AuthenticationError) {
    console.error('Authentication failed:', error.message);
  } else if (error instanceof RateLimitError) {
    console.error(`Rate limit exceeded. Retry after: ${error.retryAfter}s`);
  } else if (error instanceof ValidationError) {
    console.error('Invalid request:', error.message);
  } else if (error instanceof UtxoIQError) {
    console.error('API error:', error.message);
  }
}
```

## Configuration

### Custom Base URL

```typescript
const client = new UtxoIQClient({
  apiKey: 'your-api-key',
  baseUrl: 'https://custom-api.utxoiq.com'
});
```

### Request Timeout

```typescript
const client = new UtxoIQClient({
  apiKey: 'your-api-key',
  timeout: 30000 // milliseconds
});
```

### Retry Configuration

```typescript
const client = new UtxoIQClient({
  apiKey: 'your-api-key',
  maxRetries: 3,
  retryDelay: 1000 // milliseconds
});
```

## TypeScript Support

The SDK is written in TypeScript and provides full type definitions:

```typescript
import type {
  Insight,
  Alert,
  DailyBrief,
  ChatResponse,
  UserFeedback
} from '@utxoiq/sdk';

// All API responses are fully typed
const insight: Insight = await client.insights.getById('insight-123');
const alerts: Alert[] = await client.alerts.list();
```

## API Reference

Full API documentation is available at [https://docs.utxoiq.com/javascript-sdk](https://docs.utxoiq.com/javascript-sdk)

## Requirements

- Node.js 16+
- TypeScript 5+ (for TypeScript projects)

## Browser Support

The SDK works in modern browsers and Node.js environments. For browser usage:

```html
<script type="module">
  import { UtxoIQClient } from 'https://cdn.jsdelivr.net/npm/@utxoiq/sdk/+esm';
  
  const client = new UtxoIQClient({ apiKey: 'your-api-key' });
  const insights = await client.insights.getLatest();
</script>
```

## License

Proprietary - See LICENSE file for details

## Support

- Documentation: https://docs.utxoiq.com
- Email: api@utxoiq.com
- Issues: https://github.com/utxoiq/javascript-sdk/issues
