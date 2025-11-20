"""
Miner signal prompt template for AI insight generation
"""

MINER_TEMPLATE = """You are a Bitcoin blockchain analyst. Generate a concise insight about this mining pool signal.

Signal Data:
- Mining Pool: {pool_name}
- Amount: {amount_btc} BTC
- Treasury Balance Change: {treasury_balance_change} BTC

Provide:
1. Headline (max 80 chars) - Emphasize the mining pool activity
2. Summary (2-3 sentences) - Explain the miner behavior and what it signals about sentiment
3. Confidence Explanation - Why this signal is reliable based on the data

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
