"""
Treasury signal prompt template for AI insight generation
"""

TREASURY_TEMPLATE = """You are a Bitcoin blockchain analyst. Generate a concise insight about this corporate treasury signal.

Signal Data:
- Company: {entity_name} ({company_ticker})
- Flow Type: {flow_type}
- Amount: {amount_btc} BTC
- Known Holdings: {known_holdings_btc} BTC
- Holdings Change: {holdings_change_pct}%

Provide:
1. Headline (max 80 chars) - Mention the company name and ticker symbol
2. Summary (2-3 sentences) - Explain the corporate strategy implications and market impact
3. Confidence Explanation - Why this signal is reliable based on the data

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
