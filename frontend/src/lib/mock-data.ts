import { Insight } from '@/types';

export const MOCK_INSIGHTS: Insight[] = [
  {
    id: '1',
    signal_type: 'mempool',
    headline: 'Mempool Fees Spike to 150 sat/vB Amid High Network Activity',
    summary: 'Transaction fees have surged to 150 sat/vB as network congestion increases. This represents a 200% increase from yesterday\'s average of 50 sat/vB. Users should consider delaying non-urgent transactions.',
    confidence: 0.92,
    timestamp: new Date(Date.now() - 1000 * 60 * 15).toISOString(), // 15 min ago
    block_height: 820450,
    evidence: [
      {
        type: 'block',
        id: '00000000000000000002a7c4c1e48d76c5a37902165a270156b7a8d72728a054',
        description: 'Recent block with high fee transactions',
        url: 'https://mempool.space/block/820450',
      },
    ],
    tags: ['fees', 'congestion'],
    chart_url: undefined,
    accuracy_rating: 0.88,
  },
  {
    id: '2',
    signal_type: 'exchange',
    headline: 'Major Exchange Outflow Detected: 5,000 BTC Moved to Cold Storage',
    summary: 'A significant outflow of 5,000 BTC from Binance to unknown wallets has been detected. This could indicate institutional accumulation or preparation for OTC deals. Historical patterns suggest this is bullish for price action.',
    confidence: 0.85,
    timestamp: new Date(Date.now() - 1000 * 60 * 45).toISOString(), // 45 min ago
    block_height: 820448,
    evidence: [
      {
        type: 'transaction',
        id: 'a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6',
        description: 'Large exchange withdrawal',
        url: 'https://mempool.space/tx/a1b2c3d4',
      },
      {
        type: 'address',
        id: 'bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
        description: 'Destination cold wallet',
        url: 'https://mempool.space/address/bc1qxy2kgdygjrsqtzq2n0yrf2493p83kkfjhx0wlh',
      },
    ],
    tags: ['exchange', 'outflow', 'accumulation'],
    chart_url: undefined,
    is_predictive: true,
    accuracy_rating: 0.82,
  },
  {
    id: '3',
    signal_type: 'miner',
    headline: 'Mining Pool Consolidates 2,500 BTC - Potential Sell Pressure',
    summary: 'F2Pool has consolidated 2,500 BTC into a single address. Historical data shows that such consolidations often precede selling activity within 24-48 hours. Traders should monitor for potential downward pressure.',
    confidence: 0.78,
    timestamp: new Date(Date.now() - 1000 * 60 * 90).toISOString(), // 90 min ago
    block_height: 820445,
    evidence: [
      {
        type: 'address',
        id: '1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
        description: 'F2Pool consolidation address',
        url: 'https://mempool.space/address/1A1zP1eP5QGefi2DMPTfTL5SLmv7DivfNa',
      },
    ],
    tags: ['miner', 'consolidation', 'selling'],
    chart_url: undefined,
    is_predictive: true,
    explainability: {
      confidence_factors: {
        signal_strength: 0.82,
        historical_accuracy: 0.75,
        data_quality: 0.77,
      },
      explanation: 'This insight is based on historical patterns of miner behavior. When mining pools consolidate large amounts of BTC, it typically indicates preparation for selling or distribution.',
      supporting_evidence: [
        'Similar consolidations in the past 6 months led to selling within 48 hours in 75% of cases',
        'The consolidation size (2,500 BTC) is significant enough to impact market liquidity',
        'F2Pool has a history of regular selling to cover operational costs',
      ],
    },
  },
  {
    id: '4',
    signal_type: 'whale',
    headline: 'Whale Accumulation: 1,200 BTC Purchased Across Multiple Exchanges',
    summary: 'A coordinated buying pattern across Coinbase, Kraken, and Bitstamp suggests a single entity has accumulated 1,200 BTC in the past 2 hours. The purchases were executed in small batches to minimize price impact.',
    confidence: 0.88,
    timestamp: new Date(Date.now() - 1000 * 60 * 120).toISOString(), // 2 hours ago
    block_height: 820442,
    evidence: [
      {
        type: 'transaction',
        id: 'b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7',
        description: 'Coinbase withdrawal (400 BTC)',
        url: 'https://mempool.space/tx/b2c3d4e5',
      },
      {
        type: 'transaction',
        id: 'c3d4e5f6g7h8i9j0k1l2m3n4o5p6q7r8s9t0u1v2w3x4y5z6a7b8',
        description: 'Kraken withdrawal (500 BTC)',
        url: 'https://mempool.space/tx/c3d4e5f6',
      },
    ],
    tags: ['whale', 'accumulation', 'bullish'],
    chart_url: undefined,
    is_predictive: true,
    accuracy_rating: 0.91,
  },
  {
    id: '5',
    signal_type: 'mempool',
    headline: 'Network Congestion Easing - Fees Drop to 45 sat/vB',
    summary: 'After yesterday\'s spike, mempool congestion is clearing. Current fee estimates for next-block confirmation have dropped to 45 sat/vB. This is a good opportunity for users to process pending transactions.',
    confidence: 0.95,
    timestamp: new Date(Date.now() - 1000 * 60 * 180).toISOString(), // 3 hours ago
    block_height: 820440,
    evidence: [
      {
        type: 'block',
        id: '00000000000000000003b7c4c1e48d76c5a37902165a270156b7a8d72728a055',
        description: 'Recent block with lower fees',
        url: 'https://mempool.space/block/820440',
      },
    ],
    tags: ['fees', 'mempool', 'clearing'],
    chart_url: undefined,
  },
];
