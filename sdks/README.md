# utxoIQ SDKs

Official SDKs for the utxoIQ Bitcoin blockchain intelligence platform.

## Available SDKs

### Python SDK
- **Package**: `utxoiq`
- **PyPI**: https://pypi.org/project/utxoiq/
- **Documentation**: [Python SDK README](./python/README.md)
- **Requirements**: Python 3.9+

### JavaScript/TypeScript SDK
- **Package**: `@utxoiq/sdk`
- **npm**: https://www.npmjs.com/package/@utxoiq/sdk
- **Documentation**: [JavaScript SDK README](./javascript/README.md)
- **Requirements**: Node.js 16+

## Quick Start

### Python

```bash
pip install utxoiq
```

```python
from utxoiq import UtxoIQClient

client = UtxoIQClient(api_key="your-api-key")
insights = client.insights.get_latest(limit=10)
```

### JavaScript/TypeScript

```bash
npm install @utxoiq/sdk
```

```typescript
import { UtxoIQClient } from '@utxoiq/sdk';

const client = new UtxoIQClient({ apiKey: 'your-api-key' });
const insights = await client.insights.getLatest({ limit: 10 });
```

## Features

Both SDKs provide:

- ✅ **Type-safe API clients** with full type definitions
- ✅ **Automatic retry logic** with exponential backoff
- ✅ **Firebase Auth and API key support**
- ✅ **Comprehensive error handling**
- ✅ **Guest Mode** for public access without authentication
- ✅ **Full API coverage** for all endpoints

## Authentication

### Firebase Auth

```python
# Python
client = UtxoIQClient(firebase_token="your-jwt-token")
```

```typescript
// JavaScript/TypeScript
const client = new UtxoIQClient({ firebaseToken: 'your-jwt-token' });
```

### API Key

```python
# Python
client = UtxoIQClient(api_key="your-api-key")
```

```typescript
// JavaScript/TypeScript
const client = new UtxoIQClient({ apiKey: 'your-api-key' });
```

### Guest Mode (No Authentication)

```python
# Python
client = UtxoIQClient()  # No auth required
public_insights = client.insights.get_public(limit=20)
```

```typescript
// JavaScript/TypeScript
const client = new UtxoIQClient();  // No auth required
const publicInsights = await client.insights.getPublic({ limit: 20 });
```

## API Coverage

### Insights
- Get latest insights with filtering
- Get public insights (Guest Mode)
- Get insight by ID
- Search insights

### Alerts
- List user alerts
- Create alert
- Update alert
- Delete alert

### Feedback
- Submit insight feedback
- Get accuracy leaderboard

### Daily Brief
- Get daily brief by date
- Get latest daily brief

### Chat
- Query AI with natural language

### Billing
- Get subscription info
- Create checkout session
- Cancel subscription

### Email Preferences
- Get email preferences
- Update email preferences

## Development

### Building from Source

#### Python SDK

```bash
cd sdks/python
pip install -e ".[dev]"
pytest
```

#### JavaScript SDK

```bash
cd sdks/javascript
npm install
npm run build
npm test
```

## Publishing

SDKs are automatically published via GitHub Actions when a new release is created:

1. Create a new release on GitHub
2. GitHub Actions will:
   - Run all tests
   - Build packages
   - Publish to PyPI and npm

## Versioning

Both SDKs follow [Semantic Versioning](https://semver.org/):

- **Major**: Breaking changes
- **Minor**: New features (backward compatible)
- **Patch**: Bug fixes

## Support

- **Documentation**: https://docs.utxoiq.com
- **Email**: api@utxoiq.com
- **Issues**: 
  - Python: https://github.com/utxoiq/python-sdk/issues
  - JavaScript: https://github.com/utxoiq/javascript-sdk/issues

## License

Proprietary - See LICENSE file for details
