# Requirements Document

## Introduction

utxoIQ.com is an AI-powered intelligence platform for the Bitcoin blockchain that transforms raw Bitcoin on-chain data into interpreted, human-readable insights. The system explains not just what happened on the blockchain, but why it matters, delivering actionable insights to traders, analysts, and researchers in real time.

## Glossary

- **utxoIQ Platform**: The complete AI-powered Bitcoin blockchain intelligence system
- **Insight Engine**: The AI component that processes blockchain data and generates human-readable insights
- **Signal**: A specific type of blockchain event or pattern that the system monitors and analyzes
- **Confidence Score**: A numerical rating (0-1) indicating the reliability of an AI-generated insight
- **Daily Brief**: A curated summary of the top 3-5 blockchain events published at 7 AM UTC
- **X Bot**: Automated system that posts verified insights to X (Twitter) platform
- **Feature Engine**: Backend service that computes signals and processes blockchain data
- **Insight Feed**: Chronological display of AI-generated insights with metadata

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