# Requirements Document

## Introduction

utxoIQ.com is an AI-powered intelligence platform for the Bitcoin blockchain that transforms raw Bitcoin on-chain data into interpreted, human-readable insights. The system explains not just what happened on the blockchain, but why it matters, delivering actionable insights to traders, analysts, and researchers in real time.

This v2 specification extends the MVP with global-ready infrastructure, enhanced AI capabilities, growth-oriented features, and enterprise-grade reliability. The platform evolves from an analytics tool into a comprehensive Bitcoin intelligence layer with real-time delivery, predictive analytics, and multi-channel distribution.

## Glossary

- **utxoIQ Platform**: The complete AI-powered Bitcoin blockchain intelligence system
- **Insight Engine**: The AI component that processes blockchain data and generates human-readable insights
- **Signal**: A specific type of blockchain event or pattern that the system monitors and analyzes
- **Confidence Score**: A numerical rating (0-1) indicating the reliability of an AI-generated insight
- **Daily Brief**: A curated summary of the top 3-5 blockchain events published at 7 AM UTC
- **X Bot**: Automated system that posts verified insights to X (Twitter) platform
- **Feature Engine**: Backend service that computes signals and processes blockchain data
- **Insight Feed**: Chronological display of AI-generated insights with metadata
- **WebSocket Layer**: Real-time bidirectional communication channel for live data streaming
- **Edge Cache**: Globally distributed cache layer for low-latency content delivery
- **Predictive Signal**: Forward-looking blockchain metric forecast based on temporal models
- **Guest Mode**: Limited public access to insight feed without authentication
- **SDK**: Software Development Kit for programmatic API access
- **PWA**: Progressive Web Application for mobile-optimized experience
- **White-Label API**: Customizable API tier for enterprise integration
- **Explainability Layer**: AI transparency feature explaining confidence score rationale

## Requirements

### Requirement 1

**User Story:** As a Bitcoin trader, I want to receive real-time AI-interpreted blockchain insights, so that I can make informed trading decisions without analyzing raw data myself.

#### Acceptance Criteria

1. WHEN a new Bitcoin block is mined, THE Insight Engine SHALL process the block data within 60 seconds
2. THE utxoIQ Platform SHALL generate insights with confidence scores between 0 and 1
3. WHEN an insight has a confidence score of 0.7 or higher, THE utxoIQ Platform SHALL automatically publish the insight
4. THE utxoIQ Platform SHALL display insights in chronological order with timestamps and confidence ratings
5. THE utxoIQ Platform SHALL provide evidence citations including block heights and transaction IDs for each insight

### Requirement 2

**User Story:** As a crypto analyst, I want to access daily summarized blockchain events, so that I can quickly understand the most important developments without monitoring continuously.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL generate a Daily Brief at 7:00 AM UTC every day
2. THE Daily Brief SHALL contain the top 3-5 most significant blockchain events from the previous 24 hours
3. THE utxoIQ Platform SHALL provide shareable links for each Daily Brief
4. WHEN generating the Daily Brief, THE utxoIQ Platform SHALL rank events by significance and confidence scores
5. THE utxoIQ Platform SHALL include visual charts and evidence for each summarized event

### Requirement 3

**User Story:** As a Bitcoin researcher, I want to monitor specific blockchain metrics with custom alerts, so that I can be notified when conditions I care about occur.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL allow users to create custom alert thresholds for blockchain metrics
2. WHEN a user-defined threshold is exceeded, THE utxoIQ Platform SHALL send an alert notification
3. THE utxoIQ Platform SHALL support alerts for mempool fees, exchange inflows, and miner treasury changes
4. THE utxoIQ Platform SHALL prevent duplicate alerts within a 15-minute window for the same metric category
5. WHERE a user has a paid subscription, THE utxoIQ Platform SHALL provide advanced alert customization options

### Requirement 4

**User Story:** As a blockchain enthusiast, I want to ask natural language questions about Bitcoin data, so that I can get insights without needing technical expertise.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL provide a chat interface for natural language blockchain queries
2. WHEN a user submits a question, THE Insight Engine SHALL process the query using AI language models
3. THE utxoIQ Platform SHALL respond with relevant blockchain data and explanations
4. THE utxoIQ Platform SHALL cite specific blockchain evidence in chat responses
5. WHERE a user has a Power tier subscription, THE utxoIQ Platform SHALL provide unlimited chat queries

### Requirement 5

**User Story:** As a crypto community member, I want to follow utxoIQ insights on social media, so that I can stay informed about blockchain developments through my preferred channels.

#### Acceptance Criteria

1. THE X Bot SHALL automatically post insights with confidence scores of 0.7 or higher
2. WHEN posting to X, THE X Bot SHALL include the insight headline, chart image, and link to full details
3. THE X Bot SHALL run hourly checks for new insights ready for publication
4. THE X Bot SHALL post a daily "Bitcoin Pulse" thread at 07:00 UTC
5. THE X Bot SHALL ensure no duplicate posts within 15 minutes for the same signal category

### Requirement 6

**User Story:** As a platform user, I want to access different tiers of service based on my needs, so that I can choose the appropriate level of functionality and pay accordingly.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL provide Free, Pro, and Power subscription tiers
2. THE utxoIQ Platform SHALL authenticate users through Firebase Auth
3. THE utxoIQ Platform SHALL process payments through Stripe integration
4. WHEN a user exceeds their tier limits, THE utxoIQ Platform SHALL prompt for upgrade
5. THE utxoIQ Platform SHALL maintain 99.9% API uptime for all subscription tiers

### Requirement 7

**User Story:** As a system administrator, I want the platform to handle data anomalies gracefully, so that users receive reliable insights even when blockchain data is irregular.

#### Acceptance Criteria

1. WHEN data anomalies are detected, THE utxoIQ Platform SHALL enter "quiet mode" to prevent false insights
2. THE Feature Engine SHALL implement 6-block confirmation policy for major signals
3. THE utxoIQ Platform SHALL maintain duplicate signal rate below 0.5%
4. THE utxoIQ Platform SHALL log all data processing errors for monitoring
5. IF blockchain reorganizations occur, THEN THE utxoIQ Platform SHALL reprocess affected insights

### Requirement 8

**User Story:** As a Bitcoin network participant, I want to monitor specific signal types that matter to my role, so that I can track relevant blockchain activities efficiently.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL monitor mempool fee quantiles and block inclusion estimates
2. THE utxoIQ Platform SHALL detect exchange inflow spikes using entity-tagged anomaly detection
3. THE utxoIQ Platform SHALL track daily miner treasury balance changes per entity
4. THE utxoIQ Platform SHALL identify whale accumulation streaks over rolling 7-day periods
5. THE utxoIQ Platform SHALL generate chart snapshots in PNG format for each signal type

### Requirement 9

**User Story:** As a global Bitcoin trader, I want to receive insights with minimal latency regardless of my geographic location, so that I can act on time-sensitive blockchain events immediately.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL implement WebSocket connections for real-time insight streaming
2. WHEN a new insight is published, THE utxoIQ Platform SHALL push the update to connected clients within 2 seconds
3. THE utxoIQ Platform SHALL integrate Cloud CDN for public feed caching with edge locations
4. THE utxoIQ Platform SHALL achieve P95 latency below 200ms for cached content globally
5. THE utxoIQ Platform SHALL maintain WebSocket connection stability with automatic reconnection

### Requirement 10

**User Story:** As a prospective user, I want to explore the platform's insights without creating an account, so that I can evaluate the service before committing to a subscription.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL provide Guest Mode access to the insight feed without authentication
2. WHERE a user accesses the platform without authentication, THE utxoIQ Platform SHALL display the 20 most recent insights
3. THE utxoIQ Platform SHALL include prominent sign-up prompts in Guest Mode
4. THE utxoIQ Platform SHALL restrict advanced features in Guest Mode including alerts and chat
5. THE utxoIQ Platform SHALL track Guest Mode engagement metrics for conversion optimization

### Requirement 11

**User Story:** As a new user, I want guided onboarding that explains key features, so that I can quickly understand how to use the platform effectively.

#### Acceptance Criteria

1. WHEN a user completes registration, THE utxoIQ Platform SHALL initiate an interactive onboarding tour
2. THE utxoIQ Platform SHALL guide users through Feed, Brief, and Alerts features sequentially
3. THE utxoIQ Platform SHALL allow users to skip or dismiss the onboarding tour
4. THE utxoIQ Platform SHALL track onboarding completion rates for optimization
5. THE utxoIQ Platform SHALL provide contextual help tooltips on first interaction with key features

### Requirement 12

**User Story:** As a software developer, I want to integrate utxoIQ insights into my application programmatically, so that I can build custom tools and workflows.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL auto-generate Python and JavaScript SDKs from OpenAPI specifications
2. THE utxoIQ Platform SHALL publish SDKs to package registries with versioning
3. THE utxoIQ Platform SHALL provide comprehensive SDK documentation with code examples
4. THE utxoIQ Platform SHALL maintain SDK compatibility with API versioning
5. THE utxoIQ Platform SHALL include authentication helpers and error handling in SDKs

### Requirement 13

**User Story:** As a mobile user, I want a fast, app-like experience on my phone, so that I can monitor blockchain insights on the go.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL implement Progressive Web App capabilities with offline support
2. THE utxoIQ Platform SHALL optimize chart rendering for mobile screen sizes
3. THE utxoIQ Platform SHALL support touch gestures for chart interaction
4. THE utxoIQ Platform SHALL enable push notifications for alerts on mobile devices
5. THE utxoIQ Platform SHALL achieve Lighthouse performance score above 90 on mobile

### Requirement 14

**User Story:** As a platform operator, I want comprehensive observability into system performance, so that I can maintain SLAs and optimize costs.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL provide a Grafana dashboard displaying latency, cost, and accuracy metrics
2. THE utxoIQ Platform SHALL track block-to-insight P95 latency with alerting at 60-second threshold
3. THE utxoIQ Platform SHALL monitor AI inference costs per insight with budget alerts
4. THE utxoIQ Platform SHALL measure insight accuracy through user feedback ratings
5. THE utxoIQ Platform SHALL log all system errors with correlation IDs for debugging

### Requirement 15

**User Story:** As a Bitcoin analyst, I want predictive signals that forecast future blockchain conditions, so that I can anticipate market movements proactively.

#### Acceptance Criteria

1. THE Feature Engine SHALL generate "Next Block Fee Forecast" predictions using temporal models
2. THE Feature Engine SHALL compute "Exchange Liquidity Pressure Index" based on flow patterns
3. THE utxoIQ Platform SHALL display predictive signals with confidence intervals
4. THE utxoIQ Platform SHALL track prediction accuracy and adjust models accordingly
5. WHERE a user has a Pro or Power subscription, THE utxoIQ Platform SHALL provide access to predictive signals

### Requirement 16

**User Story:** As a user, I want to understand why the AI assigned a specific confidence score, so that I can better evaluate insight reliability.

#### Acceptance Criteria

1. WHEN displaying an insight, THE utxoIQ Platform SHALL provide an explainability summary
2. THE utxoIQ Platform SHALL explain confidence score factors including signal strength and historical accuracy
3. THE utxoIQ Platform SHALL display confidence score breakdown in a user-friendly format
4. THE utxoIQ Platform SHALL allow users to expand explainability details for deeper understanding
5. THE utxoIQ Platform SHALL use consistent explainability language across all insight types

### Requirement 17

**User Story:** As a user, I want to provide feedback on insight accuracy, so that I can help improve the AI and see which insights are most reliable.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL allow users to rate insights as "Useful" or "Not Useful"
2. WHEN a user rates an insight, THE utxoIQ Platform SHALL store the feedback for model retraining
3. THE utxoIQ Platform SHALL display aggregate accuracy ratings on insight cards
4. THE utxoIQ Platform SHALL publish a public accuracy leaderboard by model version
5. THE utxoIQ Platform SHALL use feedback data to improve confidence scoring algorithms

### Requirement 18

**User Story:** As an institutional client, I want to white-label the utxoIQ API for my organization, so that I can provide blockchain intelligence to my users under my brand.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL offer a White-Label API tier with custom branding options
2. THE utxoIQ Platform SHALL provide dedicated API endpoints with custom domain support
3. THE utxoIQ Platform SHALL allow customization of insight formatting and terminology
4. THE utxoIQ Platform SHALL provide SLA guarantees with 99.95% uptime for White-Label tier
5. THE utxoIQ Platform SHALL include priority support and dedicated account management

### Requirement 19

**User Story:** As a user receiving daily email briefs, I want the content delivered to my inbox automatically, so that I can review insights without visiting the website.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL send automated Daily Brief emails at 07:00 UTC
2. THE utxoIQ Platform SHALL format emails with responsive HTML including charts
3. THE utxoIQ Platform SHALL allow users to customize email frequency and content preferences
4. THE utxoIQ Platform SHALL track email open rates and engagement metrics
5. THE utxoIQ Platform SHALL provide unsubscribe options compliant with email regulations

### Requirement 20

**User Story:** As a platform operator, I want optimized BigQuery storage and queries, so that I can reduce costs while maintaining performance.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL implement partitioned tables for intel.signals by timestamp
2. THE utxoIQ Platform SHALL implement clustered tables for intel.insights by signal_type
3. THE utxoIQ Platform SHALL optimize query patterns to minimize full table scans
4. THE utxoIQ Platform SHALL monitor BigQuery costs with budget alerts at defined thresholds
5. THE utxoIQ Platform SHALL archive historical data older than 2 years to cold storage

### Requirement 21

**User Story:** As a platform operator, I want enhanced anomaly detection for mempool spikes and blockchain reorgs, so that the system maintains reliability during unusual network conditions.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL detect mempool fee spikes exceeding 3 standard deviations
2. WHEN a mempool spike is detected, THE utxoIQ Platform SHALL adjust confidence scoring accordingly
3. THE utxoIQ Platform SHALL detect blockchain reorganizations beyond 1 block depth
4. WHEN a reorg is detected, THE utxoIQ Platform SHALL reprocess affected insights automatically
5. THE utxoIQ Platform SHALL log all anomaly detections for operational review

### Requirement 22

**User Story:** As a platform operator, I want canary deployments with automated rollback, so that I can deploy updates safely without risking system stability.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL implement canary deployment strategy with 10% traffic routing
2. THE utxoIQ Platform SHALL monitor error rates and latency during canary deployments
3. WHEN error rates exceed 1% during canary, THE utxoIQ Platform SHALL automatically rollback
4. THE utxoIQ Platform SHALL validate OpenAPI schema compatibility before deployment
5. THE utxoIQ Platform SHALL provide deployment status dashboard with rollback controls

### Requirement 23

**User Story:** As a platform operator, I want to track AI inference costs per insight, so that I can optimize spending and pricing strategies.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL log Vertex AI API costs for each insight generation
2. THE utxoIQ Platform SHALL calculate cost per insight by signal type
3. THE utxoIQ Platform SHALL provide cost analytics dashboard with trend analysis
4. THE utxoIQ Platform SHALL alert when daily AI costs exceed budget thresholds
5. THE utxoIQ Platform SHALL optimize prompt engineering to reduce token usage

### Requirement 24

**User Story:** As a security-conscious operator, I want annual security audits and penetration testing, so that I can ensure enterprise-grade security compliance.

#### Acceptance Criteria

1. THE utxoIQ Platform SHALL undergo annual third-party security audits
2. THE utxoIQ Platform SHALL conduct penetration testing on all public-facing services
3. THE utxoIQ Platform SHALL implement IAM policy reviews quarterly
4. THE utxoIQ Platform SHALL maintain security compliance documentation
5. THE utxoIQ Platform SHALL remediate critical security findings within 30 days