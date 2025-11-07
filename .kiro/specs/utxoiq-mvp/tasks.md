# Implementation Plan

- [ ] 1. Set up project infrastructure and core data models
  - Initialize GCP project with required services (Pub/Sub, BigQuery, Cloud Run)
  - Create BigQuery datasets and table schemas for btc.blocks, btc.transactions, btc.entities, intel.insights
  - Set up development environment with Docker and local testing infrastructure
  - _Requirements: 1.1, 6.6, 7.4_

- [ ] 1.1 Create core TypeScript interfaces and data models
  - Define Insight, Signal, Citation, and Alert interfaces
  - Implement data validation schemas using Zod or similar
  - Create database connection utilities and query builders
  - _Requirements: 1.2, 1.5, 3.2, 8.1-8.5_

- [ ] 1.2 Set up Bitcoin Core node integration
  - Configure Bitcoin Core node with RPC access
  - Implement blockchain data streaming to Cloud Pub/Sub
  - Create Dataflow pipeline for data normalization and entity resolution
  - _Requirements: 1.1, 7.3, 8.1-8.5_

- [ ] 1.3 Write unit tests for data models and validation
  - Test data model validation with various input scenarios
  - Test database connection and query utilities
  - Test blockchain data parsing and normalization
  - _Requirements: 1.1, 7.3_

- [ ] 2. Implement Feature Engine for signal computation
  - Create Cloud Run service with FastAPI framework
  - Implement SignalProcessor class with core signal computation methods
  - Set up event-driven processing triggered by new blockchain data
  - _Requirements: 1.1, 8.1-8.5_

- [ ] 2.1 Implement mempool signal processing
  - Code mempool fee quantile calculation algorithms
  - Implement block inclusion time estimation logic
  - Create mempool nowcast signal generation with confidence scoring
  - _Requirements: 8.1_

- [ ] 2.2 Implement exchange flow detection
  - Code entity-tagged transaction analysis for exchange identification
  - Implement anomaly detection algorithms for unusual inflow patterns
  - Create exchange inflow spike signals with evidence citations
  - _Requirements: 8.2_

- [ ] 2.3 Implement miner treasury tracking
  - Code daily balance change calculation for mining entities
  - Implement treasury delta computation with historical comparison
  - Create miner treasury signals with entity attribution
  - _Requirements: 8.3_

- [ ] 2.4 Implement whale accumulation detection
  - Code rolling 7-day accumulation pattern analysis
  - Implement whale wallet identification and tracking logic
  - Create accumulation streak signals with confidence metrics
  - _Requirements: 8.4_

- [ ] 2.5 Write unit tests for signal processing
  - Test each signal type with historical blockchain data
  - Test confidence scoring algorithms with known events
  - Test anomaly detection with edge cases and false positives
  - _Requirements: 8.1-8.5_

- [ ] 3. Implement AI Insight Generator with Vertex AI
  - Set up Vertex AI integration with Gemini Pro model
  - Create InsightGenerator class with prompt engineering templates
  - Implement confidence calculation based on signal strength and context
  - _Requirements: 1.2, 1.3, 1.5_

- [ ] 3.1 Create insight generation prompts and templates
  - Design context-aware prompts for each signal type
  - Implement headline generation with 280-character limit for X posts
  - Create evidence citation formatting and validation
  - _Requirements: 1.5, 5.2_

- [ ] 3.2 Implement confidence scoring and filtering
  - Code confidence calculation algorithms using signal metrics
  - Implement 0.7 threshold filtering for auto-publication
  - Create quiet mode logic for data anomaly detection
  - _Requirements: 1.2, 1.3, 7.1, 7.3_

- [ ] 3.3 Write unit tests for AI insight generation
  - Test prompt templates with various signal inputs
  - Test confidence scoring with known blockchain events
  - Test quiet mode activation with anomalous data
  - _Requirements: 1.2, 1.3, 7.1_

- [ ] 4. Implement chart generation service
  - Create Cloud Run service for chart rendering using Matplotlib
  - Implement ChartRenderer class with methods for each signal type
  - Set up Cloud Storage integration for chart image hosting
  - _Requirements: 1.5, 2.2, 8.5_

- [ ] 4.1 Create chart templates for each signal type
  - Design mempool fee distribution charts with quantile visualization
  - Create exchange flow charts with timeline and volume indicators
  - Implement miner treasury charts with balance change visualization
  - Design whale accumulation charts with streak highlighting
  - _Requirements: 8.1-8.4, 8.5_

- [ ] 4.2 Implement chart generation and storage
  - Code chart rendering with consistent styling and branding
  - Implement PNG generation and compression for optimal file sizes
  - Create Cloud Storage upload with signed URL generation
  - _Requirements: 8.5_

- [ ] 4.3 Write unit tests for chart generation
  - Test chart rendering with various data scenarios
  - Test image generation and storage upload functionality
  - Test chart styling consistency across signal types
  - _Requirements: 8.5_

- [ ] 5. Create Web API service with authentication and OpenAPI v3
  - Set up FastAPI service with Cloud Run deployment and OpenAPI v3 auto-generation
  - Implement Firebase Auth integration for user authentication
  - Create RESTful endpoints for insights, alerts, and billing with comprehensive OpenAPI documentation
  - Configure automatic /docs and /redoc endpoints for interactive API documentation
  - _Requirements: 6.2, 6.4_

- [ ] 5.1 Implement public API endpoints with OpenAPI v3 schemas
  - Code /insights/latest endpoint with pagination, filtering, and comprehensive Pydantic response models
  - Implement /insight/{id} endpoint with detailed OpenAPI documentation and examples
  - Create /daily-brief/{date} endpoint with structured response schemas
  - Add OpenAPI metadata including descriptions, examples, and response codes for all endpoints
  - _Requirements: 2.1, 2.3_

- [ ] 5.2 Implement authenticated API endpoints with security schemas
  - Code /alerts CRUD endpoints with OpenAPI security definitions and user-specific filtering
  - Implement /chat/query endpoint with request/response models and Vertex AI integration
  - Create /billing/subscription endpoint with Stripe webhook schemas and validation
  - Add OpenAPI security schemes for Firebase Auth JWT tokens and API key authentication
  - _Requirements: 3.1, 3.2, 4.1, 6.3, 6.5_

- [ ] 5.3 Implement rate limiting and error handling with OpenAPI documentation
  - Code API rate limiting using Redis for request tracking with OpenAPI rate limit headers
  - Implement comprehensive error response formatting with standardized OpenAPI error schemas
  - Create subscription tier validation and feature gating with clear OpenAPI security documentation
  - _Requirements: 6.4, 6.5_

- [ ] 5.5 Set up comprehensive OpenAPI v3 documentation and tooling
  - Configure FastAPI with detailed OpenAPI metadata (title, version, description, contact info)
  - Create comprehensive Pydantic models for all request/response schemas with examples
  - Set up OpenAPI schema export endpoint (/openapi.json) for external consumption
  - Add OpenAPI tags, operation IDs, and detailed descriptions for all endpoints
  - Configure OpenAPI security schemes for Firebase Auth and API keys
  - _Requirements: 6.2, 6.4_

- [ ] 5.4 Write integration tests for API endpoints and OpenAPI validation
  - Test public endpoints with various query parameters and validate against OpenAPI schema
  - Test authenticated endpoints with different user roles and security schemes
  - Test rate limiting, error handling, and OpenAPI compliance scenarios
  - Implement automated OpenAPI schema validation in CI/CD pipeline
  - _Requirements: 3.1, 6.2, 6.4_

- [ ] 6. Build Next.js frontend application
  - Initialize Next.js 14 project with TypeScript and Tailwind CSS
  - Set up Firebase Auth integration for user authentication
  - Create responsive layout with navigation and user management
  - _Requirements: 6.2_

- [ ] 6.1 Implement insight feed and detail pages
  - Create InsightFeed component with infinite scroll and real-time updates
  - Implement InsightDetail page with charts, evidence, and sharing options
  - Add filtering and search functionality for insight discovery
  - _Requirements: 1.4, 1.5_

- [ ] 6.2 Create daily brief and summary pages
  - Implement DailyBrief component with top events and shareable links
  - Create summary cards with visual indicators and confidence scores
  - Add navigation between different daily brief dates
  - _Requirements: 2.2, 2.3, 2.4_

- [ ] 6.3 Implement alerts management interface
  - Create AlertsManager component for threshold configuration
  - Implement alert creation form with metric selection and validation
  - Add alert history and notification preferences
  - _Requirements: 3.1, 3.2, 3.5_

- [ ] 6.4 Create AI chat interface
  - Implement ChatInterface component with message history
  - Add natural language query input with suggestion prompts
  - Create response formatting with blockchain data citations
  - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [ ] 6.5 Implement billing and subscription management
  - Create BillingPortal component with Stripe integration
  - Implement subscription tier display and upgrade prompts
  - Add payment method management and billing history
  - _Requirements: 6.1, 6.3, 6.4, 6.5_

- [ ] 6.6 Write component tests for frontend
  - Test key user interactions and state management
  - Test authentication flows and protected routes
  - Test responsive design across different screen sizes
  - _Requirements: 6.2_

- [ ] 7. Implement X Bot for social media automation
  - Create Cloud Run service with X API v2 integration
  - Set up Cloud Scheduler for hourly insight polling
  - Implement tweet composition with image attachment
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [ ] 7.1 Create automated posting logic
  - Code confidence-based filtering (≥0.7) for auto-posting
  - Implement tweet formatting with headline and chart attachment
  - Create duplicate prevention using Redis for recent post tracking
  - _Requirements: 5.2, 5.3, 5.5_

- [ ] 7.2 Implement daily Bitcoin Pulse thread
  - Code daily summary generation at 7:00 AM UTC
  - Implement thread creation with multiple connected tweets
  - Add engagement tracking and performance metrics
  - _Requirements: 5.4_

- [ ] 7.3 Write integration tests for X Bot
  - Test posting workflow with mock X API responses
  - Test duplicate prevention and rate limiting
  - Test daily thread generation and scheduling
  - _Requirements: 5.1-5.5_

- [ ] 8. Set up monitoring, logging, and deployment
  - Configure Cloud Monitoring dashboards for SLA tracking
  - Set up structured logging across all services
  - Create alerting rules for system health and performance
  - _Requirements: 6.6, 7.4_

- [ ] 8.1 Implement performance monitoring
  - Code block-to-insight latency tracking with P95 metrics
  - Set up API uptime monitoring with 99.9% SLA alerting
  - Create duplicate signal rate monitoring with 0.5% threshold
  - _Requirements: 1.1, 6.6, 7.3_

- [ ] 8.2 Create deployment pipeline with OpenAPI versioning
  - Set up CI/CD with GitHub Actions and Cloud Build
  - Implement blue-green deployment strategy for zero-downtime updates
  - Create environment-specific configuration management
  - Add OpenAPI schema export and versioning to deployment pipeline (/openapi.json endpoint)
  - Set up automated OpenAPI schema diff validation for API contract testing
  - _Requirements: 6.6_

- [ ] 8.3 Write end-to-end system tests
  - Test complete data flow from Bitcoin node to insight publication
  - Test system behavior during blockchain reorganizations
  - Test failover and recovery scenarios
  - _Requirements: 7.1, 7.2, 7.5_