"""
Mempool signal prompt template for AI insight generation
"""

MEMPOOL_TEMPLATE = """You are a Bitcoin blockchain analyst. Generate a concise insight about this mempool signal.

Signal Data:
- Fee Rate (Median): {fee_rate_median} sat/vB
- Fee Rate Change: {fee_rate_change_pct}% vs previous period
- Mempool Size: {mempool_size_mb} MB
- Transaction Count: {tx_count}

Provide:
1. Headline (max 80 chars) - A clear, factual statement about the mempool state
2. Summary (2-3 sentences) - Explain what's happening and why it matters for users
3. Confidence Explanation - Why this signal is reliable based on the data

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
