# utxoIQ Shared Module

Shared TypeScript types, Zod validation schemas, and database utilities for the utxoIQ platform.

## Contents

- **types/** - Core TypeScript interfaces and type definitions
- **schemas/** - Zod validation schemas for runtime type checking
- **utils/** - Database connection utilities and query builders
- **tests/** - Unit tests for all shared code

## Installation

```bash
npm install
```

## Usage

### Types

```typescript
import { Insight, Signal, Alert } from '@utxoiq/shared/types';

const insight: Insight = {
  id: '123e4567-e89b-12d3-a456-426614174000',
  signal_type: 'mempool',
  headline: 'Mempool fees spike',
  summary: 'Network congestion detected',
  confidence: 0.85,
  timestamp: new Date(),
  block_height: 800000,
  evidence: [],
  tags: ['mempool'],
};
```

### Validation

```typescript
import { InsightSchema } from '@utxoiq/shared/schemas/validation';

const result = InsightSchema.safeParse(data);
if (result.success) {
  console.log('Valid insight:', result.data);
} else {
  console.error('Validation errors:', result.error);
}
```

### Database Utilities

```typescript
import { BigQueryInsightBuilder } from '@utxoiq/shared/utils/database';

const insights = await new BigQueryInsightBuilder()
  .whereSignalType('mempool')
  .whereConfidenceGreaterThan(0.7)
  .limit(20)
  .execute();
```

## Testing

Run tests:

```bash
npm test
```

Run tests with coverage:

```bash
npm run test:coverage
```

## Type Checking

```bash
npm run type-check
```

## Linting

```bash
npm run lint
```
