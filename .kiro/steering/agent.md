# AI Agent Guidelines

## Architecture Patterns

### Client/Server Separation
- **API-first design**: All client-server communication via REST APIs only
- **No direct database access**: Frontend never connects to databases directly
- **Stateless backend**: Services maintain no client session state
- **Clear boundaries**: Business logic on server, UI logic on client
- **Authentication flow**: Client stores tokens, server validates them
- **Data transformation**: Server provides clean JSON, client handles presentation

### Server-side Responsibilities
- Data persistence and retrieval (BigQuery, Cloud SQL, Redis)
- Business logic and data validation
- External API integrations (Bitcoin Core, Vertex AI, X API)
- Authentication and authorization (JWT validation)
- Rate limiting and security enforcement
- Background processing and scheduled tasks
- Inter-service communication via Pub/Sub

### Client-side Responsibilities
- User interface rendering and interactions
- Client-side form validation (server always validates too)
- Navigation and routing management
- Local state management (React hooks, context)
- API request orchestration and error handling
- Real-time UI updates and notifications

### Microservices Design
- Each service should have a **single responsibility**
- Use **Cloud Pub/Sub** for inter-service communication
- Implement **circuit breaker** patterns for external API calls
- Use **Redis** for caching and rate limiting
- Follow **12-factor app** principles for configuration

## Code Style & Conventions

### Python (Backend Services)
- Use **FastAPI** for all API services with async/await patterns
- Follow **PEP 8** style guidelines with 88-character line limit (Black formatter)
- Use **Pydantic** models for data validation and serialization
- Implement proper error handling with custom exception classes
- Use **type hints** for all function parameters and return values
- Structure imports: standard library, third-party, local imports

### TypeScript (Frontend & Shared)
- Use **strict TypeScript** configuration with no implicit any
- Follow **React** best practices with functional components and hooks
- Use **Tailwind CSS** for styling with component-based approach
- Implement proper error boundaries and loading states
- Use **Next.js 16** app router patterns consistently
- Prefer **server components** when possible, client components when needed

### Database & Data
- Use **snake_case** for all database table and column names
- Implement proper **BigQuery** partitioning for time-series data
- Use **Cloud SQL** for transactional data, **BigQuery** for analytics
- Always include proper indexing strategies
- Implement data validation at both API and database levels

## API Design

### RESTful Endpoints
- Use **RESTful** endpoints with proper HTTP status codes
- Implement **API versioning** (v1, v2) in URL paths
- Use **JWT tokens** for authentication with Firebase Auth
- Include **rate limiting** and **request validation**
- Provide **OpenAPI/Swagger** documentation for all endpoints

### Request/Response Patterns
- **Consistent JSON structure**: Use camelCase for JSON fields
- **Error responses**: Standardized error format across all APIs
- **Pagination**: Implement cursor-based pagination for large datasets
- **Filtering**: Support query parameters for data filtering
- **CORS**: Proper cross-origin resource sharing configuration

### Error Handling
- Use **structured logging** with correlation IDs
- Implement **graceful degradation** for non-critical features
- Return **consistent error response** formats across all services
- Use **Cloud Error Reporting** for production error tracking
- Include **blockchain citations** (block height, tx hash) in error contexts

## Bitcoin & Blockchain Specifics

### Data Processing
- Always validate **block heights** and **transaction hashes**
- Use **proper Bitcoin address** validation (P2PKH, P2SH, Bech32)
- Handle **mempool volatility** with appropriate caching strategies
- Implement **reorg detection** and handling for blockchain data
- Use **satoshi units** internally, convert to BTC for display only

### Real-time Processing
- Process new blocks within **60 seconds** of detection
- Use **streaming** patterns for high-volume transaction data
- Implement **backpressure** handling for data ingestion
- Cache frequently accessed blockchain data appropriately
- Use **batch processing** for historical data analysis

## AI & ML Integration

### Vertex AI Usage
- Use **Gemini Pro** model for insight generation
- Implement **prompt engineering** best practices
- Include **confidence scores** for all AI-generated content
- Use **structured outputs** with proper JSON schemas
- Implement **fallback strategies** for AI service failures

### Content Generation
- Always include **blockchain evidence** (citations) in insights
- Use **consistent tone** for generated content (professional, accessible)
- Implement **content moderation** for public-facing outputs
- Generate **actionable insights** rather than just data summaries
- Include **timestamp and block context** for all insights

## Security & Compliance

### Authentication & Authorization
- Use **Firebase Auth** for user management
- Implement **role-based access control** (RBAC)
- Use **API keys** for programmatic access with proper scoping
- Implement **rate limiting** per user and API key
- Log all **authentication events** for audit trails

### Data Privacy
- Never log **sensitive user data** (emails, payment info)
- Use **environment variables** for all secrets and API keys
- Implement **data retention policies** for user-generated content
- Use **Cloud Secret Manager** for production secrets
- Follow **GDPR compliance** for user data handling

## Development Workflow

### Code Quality
- Write **unit tests** for all business logic functions
- Use **integration tests** for API endpoints
- Implement **end-to-end tests** for critical user flows
- Use **pre-commit hooks** for code formatting and linting
- Maintain **test coverage** above 80% for core services

### Deployment & Monitoring
- Use **Cloud Run** for stateless services with proper health checks
- Implement **blue-green deployments** for zero-downtime updates
- Use **Cloud Monitoring** for service metrics and alerting
- Implement **distributed tracing** for request flow visibility
- Use **feature flags** for gradual rollouts of new functionality

## Performance Guidelines

### Optimization Strategies
- Use **connection pooling** for database connections
- Implement **caching layers** at multiple levels (Redis, CDN)
- Use **async processing** for non-critical operations
- Optimize **BigQuery queries** with proper partitioning and clustering
- Implement **lazy loading** for frontend components

### Scalability Considerations
- Design for **horizontal scaling** with stateless services
- Use **Cloud Load Balancing** for traffic distribution
- Implement **auto-scaling** based on CPU and memory metrics
- Use **CDN** for static assets and frequently accessed data
- Design **database schemas** for efficient querying at scale