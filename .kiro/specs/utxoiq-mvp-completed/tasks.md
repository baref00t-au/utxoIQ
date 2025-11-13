# Implementation Plan

- [x] 1. Set up project infrastructure and core data models with v2 enhancements





  - Initialize GCP project with required services (Pub/Sub, BigQuery, Cloud Run, Cloud CDN)
  - Create BigQuery datasets with partitioning and clustering for intel.signals and intel.insights
  - Set up development environment with Docker and local testing infrastructure
  - Configure Cloud CDN for edge caching with global distribution
  - _Requirements: 1.1, 6.5, 7.4, 9.3, 9.4, 20.1, 20.2_

- [x] 1.1 Create core TypeScript interfaces and data models with v2 additions


  - Define Insight, Signal, Citation, and Alert interfaces
  - Add v2 interfaces: ExplainabilitySummary, UserFeedback, PredictiveSignal, EmailPreferences, WhiteLabelConfig
  - Implement data validation schemas using Zod for all models
  - Create database connection utilities and query builders
  - _Requirements: 1.2, 1.5, 3.2, 8.1-8.5, 16.1-16.5, 17.1-17.5_

- [x] 1.2 Set up Bitcoin Core node integration with enhanced anomaly detection


  - Configure Bitcoin Core node with RPC access
  - Implement blockchain data streaming to Cloud Pub/Sub
  - Create Dataflow pipeline for data normalization and entity resolution
  - Add mempool spike detection (3 standard deviations threshold)
  - Implement blockchain reorg detection beyond 1 block depth
  - _Requirements: 1.1, 7.3, 8.1-8.5, 21.1-21.5_

- [x] 1.3 Write unit tests for data models and validation


  - Test data model validation with various input scenarios
  - Test database connection and query builders
  - Test blockchain data parsing and normalization
  - Test anomaly detection algorithms
  - _Requirements: 1.1, 7.3, 21.5_

- [x] 2. Implement Feature Engine with predictive analytics





  - Create Cloud Run service with FastAPI framework
  - Implement SignalProcessor class with core signal computation methods
  - Add PredictiveAnalytics class for forecasting capabilities
  - Set up event-driven processing triggered by new blockchain data
  - _Requirements: 1.1, 8.1-8.5, 15.1-15.5_

- [x] 2.1 Implement mempool signal processing


  - Code mempool fee quantile calculation algorithms
  - Implement block inclusion time estimation logic
  - Create mempool nowcast signal generation with confidence scoring
  - _Requirements: 8.1_

- [x] 2.2 Implement exchange flow detection


  - Code entity-tagged transaction analysis for exchange identification
  - Implement anomaly detection algorithms for unusual inflow patterns
  - Create exchange inflow spike signals with evidence citations
  - _Requirements: 8.2_

- [x] 2.3 Implement miner treasury tracking


  - Code daily balance change calculation for mining entities
  - Implement treasury delta computation with historical comparison
  - Create miner treasury signals with entity attribution
  - _Requirements: 8.3_

- [x] 2.4 Implement whale accumulation detection


  - Code rolling 7-day accumulation pattern analysis
  - Implement whale wallet identification and tracking logic
  - Create accumulation streak signals with confidence metrics
  - _Requirements: 8.4_

- [x] 2.5 Implement predictive analytics models


  - Code "Next Block Fee Forecast" using temporal models with historical mempool data
  - Implement "Exchange Liquidity Pressure Index" based on flow pattern analysis
  - Create prediction confidence interval calculations
  - Add model accuracy tracking and adjustment logic
  - _Requirements: 15.1, 15.2, 15.3, 15.4_

- [x] 2.6 Write unit tests for signal processing and predictions


  - Test each signal type with historical blockchain data
  - Test confidence scoring algorithms with known events
  - Test anomaly detection with edge cases and false positives
  - Test predictive model accuracy with historical data
  - _Requirements: 8.1-8.5, 15.4_

- [x] 3. Implement AI Insight Generator with explainability and feedback loop





  - Set up Vertex AI integration with Gemini Pro model
  - Create InsightGenerator class with prompt engineering templates
  - Implement confidence calculation based on signal strength and context
  - Add explainability layer for confidence score breakdown
  - Implement user feedback storage and processing
  - _Requirements: 1.2, 1.3, 1.5, 16.1-16.5, 17.1-17.5_


- [x] 3.1 Create insight generation prompts and templates

  - Design context-aware prompts for each signal type
  - Implement headline generation with 280-character limit for X posts
  - Create evidence citation formatting and validation
  - Add explainability prompt templates for confidence score reasoning
  - _Requirements: 1.5, 5.2, 16.2_

- [x] 3.2 Implement confidence scoring and filtering with explainability


  - Code confidence calculation algorithms using signal metrics
  - Implement 0.7 threshold filtering for auto-publication
  - Create quiet mode logic for data anomaly detection
  - Generate explainability summaries showing confidence factors
  - _Requirements: 1.2, 1.3, 7.1, 7.3, 16.1, 16.2, 16.3_

- [x] 3.3 Implement user feedback collection and processing


  - Create feedback storage in BigQuery (intel.user_feedback table)
  - Implement aggregate accuracy rating calculations
  - Build feedback loop for model retraining data collection
  - Create public accuracy leaderboard by model version
  - _Requirements: 17.1, 17.2, 17.3, 17.4, 17.5_

- [x] 3.4 Write unit tests for AI insight generation and explainability


  - Test prompt templates with various signal inputs
  - Test confidence scoring with known blockchain events
  - Test quiet mode activation with anomalous data
  - Test explainability summary generation
  - Test feedback processing and aggregation
  - _Requirements: 1.2, 1.3, 7.1, 16.5, 17.5_

- [x] 4. Implement chart generation service with mobile optimization





  - Create Cloud Run service for chart rendering using Matplotlib
  - Implement ChartRenderer class with methods for each signal type
  - Set up Cloud Storage integration for chart image hosting
  - Optimize chart rendering for mobile screen sizes
  - _Requirements: 1.5, 2.2, 8.5, 13.2_

- [x] 4.1 Create chart templates for each signal type


  - Design mempool fee distribution charts with quantile visualization
  - Create exchange flow charts with timeline and volume indicators
  - Implement miner treasury charts with balance change visualization
  - Design whale accumulation charts with streak highlighting
  - Add predictive signal charts with confidence intervals
  - _Requirements: 8.1-8.4, 8.5, 15.3_

- [x] 4.2 Implement chart generation and storage

  - Code chart rendering with consistent styling and branding
  - Implement PNG generation and compression for optimal file sizes
  - Create Cloud Storage upload with signed URL generation
  - Add responsive chart sizing for mobile devices
  - _Requirements: 8.5, 13.2_

- [x] 4.3 Write unit tests for chart generation


  - Test chart rendering with various data scenarios
  - Test image generation and storage upload functionality
  - Test chart styling consistency across signal types
  - Test mobile-optimized chart rendering
  - _Requirements: 8.5, 13.2_

- [x] 5. Create Web API service with WebSocket, authentication, and OpenAPI v3





  - Set up FastAPI service with Cloud Run deployment and OpenAPI v3 auto-generation
  - Implement WebSocket server for real-time insight streaming
  - Implement Firebase Auth integration for user authentication
  - Create RESTful endpoints for insights, alerts, billing, and feedback
  - Configure automatic /docs and /redoc endpoints for interactive API documentation
  - _Requirements: 6.2, 6.4, 9.1, 9.2, 9.5_

- [x] 5.1 Implement WebSocket layer for real-time streaming


  - Code WebSocket server with connection management
  - Implement real-time insight broadcasting to connected clients (< 2 second latency)
  - Create automatic reconnection logic for client stability
  - Add WebSocket authentication using Firebase Auth tokens
  - _Requirements: 9.1, 9.2, 9.5_

- [x] 5.2 Implement public API endpoints with Guest Mode support

  - Code /insights/latest endpoint with pagination and filtering
  - Implement /insights/public endpoint for Guest Mode (20 recent insights, no auth)
  - Create /insight/{id} endpoint with explainability data
  - Add /daily-brief/{date} endpoint with structured response schemas
  - Implement /insights/accuracy-leaderboard for public accuracy ratings
  - _Requirements: 2.1, 2.3, 10.1, 10.2, 17.4_

- [x] 5.3 Implement authenticated API endpoints with feedback and preferences

  - Code /alerts CRUD endpoints with user-specific filtering
  - Implement /chat/query endpoint with Vertex AI integration
  - Create /billing/subscription endpoint with Stripe integration
  - Add /insights/{id}/feedback endpoint for user ratings
  - Implement /email/preferences endpoint for email customization
  - _Requirements: 3.1, 3.2, 4.1, 6.3, 6.5, 17.1, 19.3_

- [x] 5.4 Implement White-Label API tier endpoints


  - Create custom branded API endpoints with client-specific prefixes
  - Implement custom domain support for White-Label clients
  - Add insight formatting customization per client configuration
  - Create dedicated SLA monitoring for White-Label tier (99.95% uptime)
  - _Requirements: 18.1, 18.2, 18.3, 18.4_

- [x] 5.5 Implement rate limiting and error handling


  - Code API rate limiting using Redis for request tracking
  - Implement comprehensive error response formatting with standardized schemas
  - Create subscription tier validation and feature gating
  - Add cost tracking for AI inference per insight
  - _Requirements: 6.4, 6.5, 23.1, 23.2_

- [x] 5.6 Set up comprehensive OpenAPI v3 documentation for SDK generation


  - Configure FastAPI with detailed OpenAPI metadata
  - Create comprehensive Pydantic models for all request/response schemas with examples
  - Set up OpenAPI schema export endpoint (/openapi.json)
  - Add OpenAPI tags, operation IDs, and detailed descriptions
  - Configure OpenAPI security schemes for Firebase Auth and API keys
  - _Requirements: 6.2, 6.4, 12.1_

- [x] 5.7 Write integration tests for API endpoints and WebSocket


  - Test public endpoints with various query parameters
  - Test authenticated endpoints with different user roles
  - Test WebSocket connection stability and message delivery
  - Test rate limiting and error handling scenarios
  - Test Guest Mode access restrictions
  - Implement automated OpenAPI schema validation in CI/CD
  - _Requirements: 3.1, 6.2, 6.4, 9.5, 10.4_

- [x] 6. Build Next.js PWA frontend with v2 enhancements





  - Initialize Next.js 16 project with TypeScript and Tailwind CSS
  - Set up Firebase Auth integration for user authentication
  - Configure PWA capabilities with service worker and manifest
  - Create responsive layout with navigation and user management
  - Implement WebSocket client for real-time updates
  - _Requirements: 6.2, 13.1, 13.5_

- [x] 6.1 Implement insight feed with real-time updates and Guest Mode


  - Create InsightFeed component with infinite scroll
  - Integrate WebSocket client for live insight streaming
  - Implement Guest Mode view (20 recent insights, prominent sign-up prompts)
  - Add filtering and search functionality for insight discovery
  - Track Guest Mode engagement metrics for conversion optimization
  - _Requirements: 1.4, 1.5, 9.2, 10.1, 10.2, 10.3, 10.5_

- [x] 6.2 Implement insight detail page with explainability


  - Create InsightDetail page with charts and evidence
  - Add explainability panel showing confidence score breakdown
  - Implement expandable explainability details section
  - Add user feedback widget (Useful/Not Useful ratings)
  - Display aggregate accuracy ratings on insight cards
  - _Requirements: 1.5, 16.1, 16.3, 16.4, 17.1, 17.3_

- [x] 6.3 Create daily brief and summary pages


  - Implement DailyBrief component with top events and shareable links
  - Create summary cards with visual indicators and confidence scores
  - Add navigation between different daily brief dates
  - _Requirements: 2.2, 2.3, 2.4_

- [x] 6.4 Implement alerts management interface with push notifications


  - Create AlertsManager component for threshold configuration
  - Implement alert creation form with metric selection and validation
  - Add alert history and notification preferences
  - Enable push notifications for mobile devices
  - _Requirements: 3.1, 3.2, 3.5, 13.4_

- [x] 6.5 Create AI chat interface


  - Implement ChatInterface component with message history
  - Add natural language query input with suggestion prompts
  - Create response formatting with blockchain data citations
  - _Requirements: 4.2, 4.3, 4.4, 4.5_

- [x] 6.6 Implement billing and subscription management


  - Create BillingPortal component with Stripe integration
  - Implement subscription tier display and upgrade prompts
  - Add payment method management and billing history
  - Show predictive signals access for Pro/Power tiers
  - _Requirements: 6.1, 6.3, 6.4, 6.5, 15.5_

- [x] 6.7 Implement interactive onboarding tour


  - Create onboarding tour component triggered after registration
  - Guide users through Feed → Brief → Alerts features sequentially
  - Add skip/dismiss functionality for onboarding tour
  - Track onboarding completion rates for optimization
  - Implement contextual help tooltips on first feature interaction
  - _Requirements: 11.1, 11.2, 11.3, 11.4, 11.5_

- [x] 6.8 Optimize PWA features for mobile


  - Configure service worker for offline support
  - Implement touch gestures for chart interaction
  - Optimize chart rendering for mobile screen sizes
  - Create app manifest for installability
  - Achieve Lighthouse performance score > 90 on mobile
  - _Requirements: 13.1, 13.2, 13.3, 13.5_

- [x] 6.9 Write component tests for frontend


  - Test key user interactions and state management
  - Test authentication flows and protected routes
  - Test responsive design across different screen sizes
  - Test WebSocket connection and real-time updates
  - Test Guest Mode restrictions and sign-up prompts
  - Test onboarding tour flow and completion tracking
  - _Requirements: 6.2, 10.4, 11.4_

- [x] 7. Implement X Bot for social media automation





  - Create Cloud Run service with X API v2 integration
  - Set up Cloud Scheduler for hourly insight polling
  - Implement tweet composition with image attachment
  - _Requirements: 5.1, 5.2, 5.3, 5.4, 5.5_

- [x] 7.1 Create automated posting logic


  - Code confidence-based filtering (≥0.7) for auto-posting
  - Implement tweet formatting with headline and chart attachment
  - Create duplicate prevention using Redis for recent post tracking
  - _Requirements: 5.2, 5.3, 5.5_

- [x] 7.2 Implement daily Bitcoin Pulse thread


  - Code daily summary generation at 7:00 AM UTC
  - Implement thread creation with multiple connected tweets
  - Add engagement tracking and performance metrics
  - _Requirements: 5.4_

- [x] 7.3 Write integration tests for X Bot


  - Test posting workflow with mock X API responses
  - Test duplicate prevention and rate limiting
  - Test daily thread generation and scheduling
  - _Requirements: 5.1-5.5_

- [x] 8. Implement Email Service for Daily Briefs





  - Create Cloud Run service with SendGrid or Mailgun integration
  - Implement scheduled Daily Brief email delivery at 07:00 UTC
  - Create responsive HTML email templates with embedded charts
  - Set up email engagement tracking (open rates, click-through)
  - _Requirements: 19.1, 19.2, 19.4_

- [x] 8.1 Create email template and preference management


  - Design responsive HTML email templates for Daily Briefs
  - Implement email preference management (frequency, content filters)
  - Add unsubscribe functionality compliant with email regulations
  - Create user preference storage in BigQuery
  - _Requirements: 19.2, 19.3, 19.5_

- [x] 8.2 Write integration tests for email service


  - Test email template rendering with various brief content
  - Test scheduled delivery at 07:00 UTC
  - Test preference management and unsubscribe flow
  - Test engagement tracking functionality
  - _Requirements: 19.1, 19.4_

- [x] 9. Set up SDK auto-generation and publishing





  - Configure OpenAPI Generator for Python and JavaScript SDKs
  - Set up GitHub Actions workflow for automated SDK generation
  - Create SDK documentation with code examples
  - Publish SDKs to PyPI and npm with semantic versioning
  - _Requirements: 12.1, 12.2, 12.3, 12.4, 12.5_

- [x] 9.1 Generate and configure Python SDK


  - Auto-generate Python SDK from OpenAPI spec
  - Add authentication helpers for Firebase Auth and API keys
  - Implement error handling and retry logic
  - Create comprehensive documentation with examples
  - Publish to PyPI with versioning
  - _Requirements: 12.1, 12.2, 12.3, 12.5_

- [x] 9.2 Generate and configure JavaScript/TypeScript SDK


  - Auto-generate JS/TS SDK from OpenAPI spec
  - Add type-safe API client with TypeScript definitions
  - Implement authentication helpers and error handling
  - Create comprehensive documentation with examples
  - Publish to npm with versioning
  - _Requirements: 12.1, 12.2, 12.3, 12.5_

- [x] 9.3 Write tests for generated SDKs


  - Test Python SDK with various API endpoints
  - Test JavaScript SDK with various API endpoints
  - Test authentication flows in both SDKs
  - Test error handling and retry logic
  - _Requirements: 12.4, 12.5_

- [x] 10. Set up Grafana observability dashboard





  - Configure Grafana with Cloud Monitoring integration
  - Create dashboards for latency, cost, and accuracy metrics
  - Set up alerting rules for SLA compliance
  - Implement cost tracking for AI inference and BigQuery
  - _Requirements: 14.1, 14.2, 14.3, 14.4, 14.5, 23.1, 23.2, 23.3, 23.4_

- [x] 10.1 Create performance monitoring dashboards


  - Build dashboard for block-to-insight P95 latency tracking
  - Create API uptime monitoring with 99.9% SLA tracking
  - Add WebSocket connection stability metrics
  - Implement duplicate signal rate monitoring (< 0.5% threshold)
  - Set up alerting at 60-second latency threshold
  - _Requirements: 1.1, 6.5, 7.3, 14.2_

- [x] 10.2 Create cost tracking and analytics dashboards


  - Build dashboard for AI inference costs per insight by signal type
  - Create BigQuery cost monitoring with query performance metrics
  - Implement budget alerts for daily AI and BigQuery costs
  - Add cost trend analysis and optimization recommendations
  - _Requirements: 14.3, 23.1, 23.2, 23.3, 23.4, 23.5_

- [x] 10.3 Create accuracy and feedback dashboards


  - Build dashboard for insight accuracy through user feedback ratings
  - Create public accuracy leaderboard by model version
  - Add prediction accuracy tracking for predictive signals
  - Implement correlation IDs for error debugging
  - _Requirements: 14.4, 14.5, 15.4, 17.4_

- [x] 11. Optimize BigQuery storage and queries





  - Implement partitioned tables for intel.signals by timestamp
  - Implement clustered tables for intel.insights by signal_type
  - Optimize query patterns to minimize full table scans
  - Set up BigQuery cost monitoring with budget alerts
  - Create data archival strategy for historical data (> 2 years to cold storage)
  - _Requirements: 20.1, 20.2, 20.3, 20.4, 20.5_

- [x] 12. Set up monitoring, logging, and canary deployment




  - Configure Cloud Monitoring dashboards for SLA tracking
  - Set up structured logging across all services with correlation IDs
  - Create alerting rules for system health and performance
  - Implement canary deployment strategy with automated rollback
  - _Requirements: 6.5, 7.4, 14.5, 22.1-22.5_

- [x] 12.1 Implement canary deployment with automated rollback



  - Configure canary deployment with 10% traffic routing
  - Implement error rate and latency monitoring during canary
  - Create automated rollback logic when error rate > 1%
  - Add OpenAPI schema compatibility validation before deployment
  - Build deployment status dashboard with rollback controls
  - _Requirements: 22.1, 22.2, 22.3, 22.4, 22.5_

- [x] 12.2 Create deployment pipeline with OpenAPI versioning


  - Set up CI/CD with GitHub Actions and Cloud Build
  - Implement blue-green deployment strategy for zero-downtime updates
  - Create environment-specific configuration management
  - Add OpenAPI schema export and versioning to deployment pipeline
  - Set up automated OpenAPI schema diff validation for API contract testing
  - Integrate SDK generation into deployment pipeline
  - _Requirements: 6.5, 12.1, 22.4_

- [x] 12.3 Write end-to-end system tests


  - Test complete data flow from Bitcoin node to insight publication
  - Test system behavior during blockchain reorganizations
  - Test failover and recovery scenarios
  - Test canary deployment and rollback functionality
  - Test WebSocket connection stability under load
  - _Requirements: 7.1, 7.2, 7.5, 21.4, 22.3_

- [x] 13. Implement security audits and compliance





  - Schedule annual third-party security audits
  - Conduct penetration testing on all public-facing services
  - Implement quarterly IAM policy reviews
  - Maintain security compliance documentation
  - Create remediation process for critical security findings (< 30 days)
  - _Requirements: 24.1, 24.2, 24.3, 24.4, 24.5_
