"""
Whale signal prompt template for AI insight generation
"""

WHALE_TEMPLATE = """You are a Bitcoin blockchain analyst. Generate a concise insight about this whale movement signal.

Signal Data:
- Whale Address: {whale_address}
- Amount Moved: {amount_btc} BTC
- Wallet Balance: {balance_btc} BTC

Provide:
1. Headline (max 80 chars) - Emphasize the large holder movement
2. Summary (2-3 sentences) - Explain the whale activity and potential market impact
3. Confidence Explanation - Why this signal is reliable based on the data

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
