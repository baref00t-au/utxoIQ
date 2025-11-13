# Design Document

## Overview

This design implements a comprehensive testing and quality assurance system using pytest for backend testing, Vitest and React Testing Library for frontend testing, Playwright for end-to-end testing, GitHub Actions for CI/CD, and various tools for security, performance, and accessibility testing.

## Architecture

### Testing Architecture

```
┌─────────────────────────────────────────────────┐
│              GitHub Actions CI/CD                │
└────────┬────────────────────────────────────────┘
         │
    ┌────┴────┐
    │         │
┌───▼───┐ ┌──▼────┐
│ Lint  │ │ Type  │
│ Check │ │ Check │
└───┬───┘ └───┬───┘
    │         │
    └────┬────┘
         │
    ┌────▼────────────────────────┐
    │      Run Tests              │
    ├─────────────────────────────┤
    │ • Unit Tests (pytest/vitest)│
    │ • Integration Tests         │
    │ • E2E Tests (Playwright)    │
    │ • Security Tests            │
    │ • Accessibility Tests       │
    └────┬────────────────────────┘
         │
    ┌────▼────┐
    │Coverage │
    │ Report  │
    └────┬────┘
         │
    ┌────▼────┐
    │ Deploy  │
    │ Staging │
    └────┬────┘
         │
    ┌────▼────┐
    │ Manual  │
    │Approval │
    └────┬────┘
         │
    ┌────▼────┐
    │ Deploy  │
    │  Prod   │
    └─────────┘
```

## Components and Interfaces

### 1. Backend Unit Testing (pytest)

#### Test Configuration
```python
# tests/conftest.py
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from app.database import Base
from app.main import app

@pytest.fixture(scope="session")
def test_db():
    """Create test database"""
    engine = create_engine("postgresql://test:test@localhost/test_utxoiq")
    Base.metadata.create_all(engine)
    yield engine
    Base.metadata.drop_all(engine)

@pytest.fixture
def db_session(test_db):
    """Provide clean database session for each test"""
    Session = sessionmaker(bind=test_db)
    session = Session()
    yield session
    session.rollback()
    session.close()

@pytest.fixture
def client():
    """Provide test client"""
    from fastapi.testclient import TestClient
    return TestClient(app)

@pytest.fixture
def auth_headers(client):
    """Provide authenticated request headers"""
    # Create test user and get token
    response = client.post("/api/v1/auth/login", json={
        "email": "test@example.com",
        "password": "testpass123"
    })
    token = response.json()["access_token"]
    return {"Authorization": f"Bearer {token}"}
```

#### Example Unit Tests
```python
# tests/test_insights.py
import pytest
from app.services.insight_service import InsightService

def test_create_insight(db_session):
    """Test insight creation"""
    service = InsightService(db_session)
    insight = service.create_insight({
        "title": "Test Insight",
        "category": "mempool",
        "confidence": 0.85
    })
    
    assert insight.id is not None
    assert insight.title == "Test Insight"
    assert insight.confidence == 0.85

def test_get_insights_with_filters(db_session):
    """Test insight filtering"""
    service = InsightService(db_session)
    
    # Create test data
    service.create_insight({"title": "High Confidence", "confidence": 0.9})
    service.create_insight({"title": "Low Confidence", "confidence": 0.5})
    
    # Test filter
    results = service.get_insights(min_confidence=0.7)
    assert len(results) == 1
    assert results[0].title == "High Confidence"

def test_api_endpoint(client, auth_headers):
    """Test API endpoint"""
    response = client.get("/api/v1/insights", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list)
```

### 2. Frontend Unit Testing (Vitest + React Testing Library)

#### Test Configuration
```typescript
// vitest.config.ts
import { defineConfig } from 'vitest/config';
import react from '@vitejs/plugin-react';

export default defineConfig({
  plugins: [react()],
  test: {
    environment: 'jsdom',
    setupFiles: ['./tests/setup.ts'],
    coverage: {
      provider: 'v8',
      reporter: ['text', 'json', 'html'],
      exclude: ['node_modules/', 'tests/'],
      thresholds: {
        lines: 80,
        functions: 80,
        branches: 80,
        statements: 80,
      },
    },
  },
});
```

#### Example Component Tests
```typescript
// tests/components/InsightCard.test.tsx
import { render, screen, fireEvent } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { InsightCard } from '@/components/InsightCard';

describe('InsightCard', () => {
  const mockInsight = {
    id: '1',
    title: 'Test Insight',
    summary: 'Test summary',
    category: 'mempool',
    confidence: 0.85,
    createdAt: '2024-01-01T00:00:00Z',
  };
  
  it('renders insight data correctly', () => {
    render(<InsightCard insight={mockInsight} />);
    
    expect(screen.getByText('Test Insight')).toBeInTheDocument();
    expect(screen.getByText('Test summary')).toBeInTheDocument();
    expect(screen.getByText('85%')).toBeInTheDocument();
  });
  
  it('calls onClick when clicked', () => {
    const handleClick = vi.fn();
    render(<InsightCard insight={mockInsight} onClick={handleClick} />);
    
    fireEvent.click(screen.getByRole('article'));
    expect(handleClick).toHaveBeenCalledWith(mockInsight.id);
  });
  
  it('displays confidence badge with correct color', () => {
    render(<InsightCard insight={mockInsight} />);
    
    const badge = screen.getByText('85%');
    expect(badge).toHaveClass('bg-green-500'); // High confidence
  });
});
```

#### Example Hook Tests
```typescript
// tests/hooks/useAuth.test.ts
import { renderHook, waitFor } from '@testing-library/react';
import { describe, it, expect, vi } from 'vitest';
import { useAuth } from '@/lib/auth';

describe('useAuth', () => {
  it('returns null user when not authenticated', () => {
    const { result } = renderHook(() => useAuth());
    expect(result.current.user).toBeNull();
  });
  
  it('signs in user successfully', async () => {
    const { result } = renderHook(() => useAuth());
    
    await result.current.signIn('test@example.com', 'password');
    
    await waitFor(() => {
      expect(result.current.user).not.toBeNull();
      expect(result.current.user?.email).toBe('test@example.com');
    });
  });
});
```

### 3. Integration Testing

```python
# tests/integration/test_auth_flow.py
import pytest
from fastapi.testclient import TestClient

def test_complete_auth_flow(client):
    """Test complete authentication flow"""
    # Register
    response = client.post("/api/v1/auth/register", json={
        "email": "newuser@example.com",
        "password": "securepass123"
    })
    assert response.status_code == 201
    
    # Login
    response = client.post("/api/v1/auth/login", json={
        "email": "newuser@example.com",
        "password": "securepass123"
    })
    assert response.status_code == 200
    token = response.json()["access_token"]
    
    # Access protected endpoint
    headers = {"Authorization": f"Bearer {token}"}
    response = client.get("/api/v1/auth/profile", headers=headers)
    assert response.status_code == 200
    assert response.json()["email"] == "newuser@example.com"

def test_database_persistence(client, db_session):
    """Test data persists across requests"""
    # Create insight
    response = client.post("/api/v1/insights", json={
        "title": "Persistent Insight",
        "category": "mempool"
    })
    insight_id = response.json()["id"]
    
    # Retrieve insight
    response = client.get(f"/api/v1/insights/{insight_id}")
    assert response.status_code == 200
    assert response.json()["title"] == "Persistent Insight"
```

### 4. End-to-End Testing (Playwright)

#### Playwright Configuration
```typescript
// playwright.config.ts
import { defineConfig, devices } from '@playwright/test';

export default defineConfig({
  testDir: './tests/e2e',
  fullyParallel: true,
  forbidOnly: !!process.env.CI,
  retries: process.env.CI ? 2 : 0,
  workers: process.env.CI ? 1 : undefined,
  reporter: 'html',
  use: {
    baseURL: 'http://localhost:3000',
    trace: 'on-first-retry',
    screenshot: 'only-on-failure',
  },
  projects: [
    {
      name: 'chromium',
      use: { ...devices['Desktop Chrome'] },
    },
    {
      name: 'firefox',
      use: { ...devices['Desktop Firefox'] },
    },
    {
      name: 'webkit',
      use: { ...devices['Desktop Safari'] },
    },
    {
      name: 'Mobile Chrome',
      use: { ...devices['Pixel 5'] },
    },
  ],
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
  },
});
```

#### Example E2E Tests
```typescript
// tests/e2e/auth.spec.ts
import { test, expect } from '@playwright/test';

test.describe('Authentication', () => {
  test('user can sign up and log in', async ({ page }) => {
    // Navigate to sign up
    await page.goto('/sign-up');
    
    // Fill form
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Verify redirect to dashboard
    await expect(page).toHaveURL('/dashboard');
    
    // Verify user is logged in
    await expect(page.locator('text=test@example.com')).toBeVisible();
  });
  
  test('user can view insights', async ({ page }) => {
    // Login first
    await page.goto('/sign-in');
    await page.fill('input[name="email"]', 'test@example.com');
    await page.fill('input[name="password"]', 'password123');
    await page.click('button[type="submit"]');
    
    // Navigate to insights
    await page.goto('/');
    
    // Verify insights are displayed
    await expect(page.locator('[data-testid="insight-card"]')).toHaveCount(10);
  });
});
```

### 5. CI/CD Pipeline (GitHub Actions)

```yaml
# .github/workflows/ci.yml
name: CI/CD Pipeline

on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]

jobs:
  lint-and-type-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: |
          pip install black flake8 mypy
          pip install -r requirements.txt
      
      - name: Run Black
        run: black --check .
      
      - name: Run Flake8
        run: flake8 .
      
      - name: Run MyPy
        run: mypy .
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install frontend dependencies
        run: npm ci
      
      - name: Run ESLint
        run: npm run lint
      
      - name: Run TypeScript check
        run: npm run type-check

  backend-tests:
    runs-on: ubuntu-latest
    needs: lint-and-type-check
    
    services:
      postgres:
        image: postgres:15
        env:
          POSTGRES_PASSWORD: postgres
        options: >-
          --health-cmd pg_isready
          --health-interval 10s
          --health-timeout 5s
          --health-retries 5
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Python
        uses: actions/setup-python@v4
        with:
          python-version: '3.12'
      
      - name: Install dependencies
        run: pip install -r requirements.txt
      
      - name: Run unit tests
        run: pytest tests/unit --cov=app --cov-report=xml
      
      - name: Run integration tests
        run: pytest tests/integration --cov=app --cov-append --cov-report=xml
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage.xml
          flags: backend

  frontend-tests:
    runs-on: ubuntu-latest
    needs: lint-and-type-check
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Run unit tests
        run: npm run test:coverage
      
      - name: Upload coverage
        uses: codecov/codecov-action@v3
        with:
          files: ./coverage/coverage-final.json
          flags: frontend

  e2e-tests:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests]
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Set up Node.js
        uses: actions/setup-node@v3
        with:
          node-version: '18'
      
      - name: Install dependencies
        run: npm ci
      
      - name: Install Playwright
        run: npx playwright install --with-deps
      
      - name: Run E2E tests
        run: npm run test:e2e
      
      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/

  security-tests:
    runs-on: ubuntu-latest
    needs: lint-and-type-check
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Run Snyk security scan
        uses: snyk/actions/python@master
        env:
          SNYK_TOKEN: ${{ secrets.SNYK_TOKEN }}
      
      - name: Run npm audit
        run: npm audit --audit-level=high
      
      - name: Run Bandit (Python security)
        run: |
          pip install bandit
          bandit -r app/

  deploy-staging:
    runs-on: ubuntu-latest
    needs: [backend-tests, frontend-tests, e2e-tests, security-tests]
    if: github.ref == 'refs/heads/main'
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Cloud Run (Staging)
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: utxoiq-api-staging
          region: us-central1
          source: .
          credentials: ${{ secrets.GCP_SA_KEY }}

  deploy-production:
    runs-on: ubuntu-latest
    needs: deploy-staging
    if: github.ref == 'refs/heads/main'
    environment:
      name: production
      url: https://utxoiq.com
    
    steps:
      - uses: actions/checkout@v3
      
      - name: Deploy to Cloud Run (Production)
        uses: google-github-actions/deploy-cloudrun@v1
        with:
          service: utxoiq-api
          region: us-central1
          source: .
          credentials: ${{ secrets.GCP_SA_KEY }}
```

### 6. Load Testing (Locust)

```python
# tests/load/locustfile.py
from locust import HttpUser, task, between

class UtxoIQUser(HttpUser):
    wait_time = between(1, 3)
    
    def on_start(self):
        """Login before starting tasks"""
        response = self.client.post("/api/v1/auth/login", json={
            "email": "loadtest@example.com",
            "password": "testpass123"
        })
        self.token = response.json()["access_token"]
        self.headers = {"Authorization": f"Bearer {self.token}"}
    
    @task(3)
    def view_insights(self):
        """View insights list"""
        self.client.get("/api/v1/insights", headers=self.headers)
    
    @task(2)
    def view_insight_detail(self):
        """View single insight"""
        self.client.get("/api/v1/insights/123", headers=self.headers)
    
    @task(1)
    def create_alert(self):
        """Create alert"""
        self.client.post("/api/v1/alerts", headers=self.headers, json={
            "metric": "mempool_fee",
            "threshold": 50,
            "channel": "email"
        })
```

### 7. Test Fixtures

```python
# tests/fixtures/insights.py
from faker import Faker
import random

fake = Faker()

def create_insight_fixture(category=None, confidence=None):
    """Create realistic insight test data"""
    return {
        "id": fake.uuid4(),
        "title": fake.sentence(nb_words=8),
        "summary": fake.paragraph(nb_sentences=3),
        "category": category or random.choice(['mempool', 'exchange', 'miner', 'whale']),
        "confidence": confidence or random.uniform(0.5, 1.0),
        "created_at": fake.date_time_this_month().isoformat(),
        "evidence": {
            "blocks": [random.randint(800000, 850000) for _ in range(3)],
            "txids": [fake.sha256() for _ in range(5)]
        }
    }

def create_user_fixture(role="user", tier="free"):
    """Create user test data"""
    return {
        "id": fake.uuid4(),
        "email": fake.email(),
        "display_name": fake.name(),
        "role": role,
        "subscription_tier": tier,
        "created_at": fake.date_time_this_year().isoformat()
    }
```

## Testing Strategy

### Test Pyramid
- **Unit Tests (70%)**: Fast, isolated tests of individual functions
- **Integration Tests (20%)**: Tests of component interactions
- **E2E Tests (10%)**: Tests of complete user workflows

### Coverage Goals
- Backend: 80%+ line coverage
- Frontend: 80%+ line coverage
- Critical paths: 100% coverage

### Test Execution
- Unit tests: Run on every commit
- Integration tests: Run on every PR
- E2E tests: Run on every PR and before deployment
- Load tests: Run weekly and before major releases
- Security tests: Run daily

## Configuration

### Environment Variables
```bash
# Testing
TEST_DATABASE_URL=postgresql://test:test@localhost/test_utxoiq
TEST_REDIS_URL=redis://localhost:6379/1
CI=true

# Coverage
COVERAGE_THRESHOLD=80

# Load Testing
LOCUST_USERS=1000
LOCUST_SPAWN_RATE=10
LOCUST_RUN_TIME=5m
```

## Deployment Considerations

### Staging Environment
- Separate GCP project
- Identical infrastructure to production
- Automatic deployments from main branch
- Weekly data reset

### Production Deployment
- Manual approval required
- Blue-green deployment strategy
- Automatic health checks
- Rollback on failure

### Monitoring
- Track test execution times
- Monitor test flakiness
- Alert on coverage drops
- Track deployment success rate
