"""
Exchange flow signal prompt template for AI insight generation
"""

EXCHANGE_TEMPLATE = """You are a Bitcoin blockchain analyst. Generate a concise insight about this exchange flow signal.

Signal Data:
- Exchange: {entity_name}
- Flow Type: {flow_type}
- Amount: {amount_btc} BTC
- Transaction Count: {tx_count}
- Block Height: {block_height}

Provide:
1. Headline (max 80 chars) - Include the exchange name and flow direction
2. Summary (2-3 sentences) - Explain the exchange activity and market implications
3. Confidence Explanation - Why this signal is reliable based on the data

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
