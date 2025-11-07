"""
Prompt templates for AI insight generation
Context-aware prompts for each signal type with explainability
"""

from typing import Dict, Any


class PromptTemplates:
    """Prompt templates for different signal types"""
    
    # Base system prompt for all insights
    SYSTEM_PROMPT = """You are an expert Bitcoin blockchain analyst for utxoIQ, an AI-powered intelligence platform.
Your role is to transform raw blockchain signals into clear, actionable insights for traders, analysts, and researchers.

Guidelines:
- Be factual and precise, avoiding speculation
- Use professional but accessible language
- Focus on "why it matters" not just "what happened"
- Include specific blockchain evidence (block heights, transaction counts)
- Keep tone calm and analytical
- Avoid hyperbole or sensationalism
- Provide context for significance
"""

    # Mempool signal prompts
    MEMPOOL_PROMPT = """Analyze this mempool signal and generate an insight:

Signal Data:
- Block Height: {block_height}
- Fee Quantiles (sat/vB): P25={p25}, P50={p50}, P75={p75}, P95={p95}
- Mempool Size: {mempool_size} transactions
- Estimated Next Block Fee: {next_block_fee} sat/vB
- Signal Strength: {signal_strength}

Context:
- Historical average P50: {historical_p50} sat/vB
- 24h change: {change_24h}%
- Anomaly detected: {is_anomaly}

Generate:
1. A headline (max 280 characters) that captures the key insight
2. A 2-3 sentence summary explaining what's happening and why it matters
3. List 2-3 pieces of supporting evidence from the data
4. Suggest what this means for users (traders, analysts)

Format your response as JSON:
{{
  "headline": "...",
  "summary": "...",
  "supporting_evidence": ["...", "...", "..."],
  "user_impact": "..."
}}
"""

    EXCHANGE_FLOW_PROMPT = """Analyze this exchange flow signal and generate an insight:

Signal Data:
- Block Height: {block_height}
- Exchange: {exchange_name}
- Inflow Amount: {inflow_btc} BTC
- Transaction Count: {tx_count}
- Anomaly Score: {anomaly_score}
- Signal Strength: {signal_strength}

Context:
- 7-day average inflow: {avg_inflow_7d} BTC
- Standard deviation: {std_dev} BTC
- This inflow is {std_dev_multiple}x standard deviations above average
- Historical context: {historical_context}

Generate:
1. A headline (max 280 characters) highlighting the unusual activity
2. A 2-3 sentence summary explaining the significance
3. List 2-3 pieces of supporting evidence
4. Explain potential market implications

Format your response as JSON:
{{
  "headline": "...",
  "summary": "...",
  "supporting_evidence": ["...", "...", "..."],
  "user_impact": "..."
}}
"""

    MINER_TREASURY_PROMPT = """Analyze this miner treasury signal and generate an insight:

Signal Data:
- Block Height: {block_height}
- Mining Entity: {entity_name}
- Daily Balance Change: {balance_change} BTC
- Current Treasury: {current_balance} BTC
- Signal Strength: {signal_strength}

Context:
- 30-day average change: {avg_change_30d} BTC
- Trend: {trend} (accumulating/distributing)
- Historical pattern: {historical_pattern}
- Market context: {market_context}

Generate:
1. A headline (max 280 characters) about the miner activity
2. A 2-3 sentence summary explaining the behavior and significance
3. List 2-3 pieces of supporting evidence
4. Explain what this signals about miner sentiment

Format your response as JSON:
{{
  "headline": "...",
  "summary": "...",
  "supporting_evidence": ["...", "...", "..."],
  "user_impact": "..."
}}
"""

    WHALE_ACCUMULATION_PROMPT = """Analyze this whale accumulation signal and generate an insight:

Signal Data:
- Block Height: {block_height}
- Wallet Address: {address_prefix}...
- 7-day Accumulation: {accumulation_btc} BTC
- Accumulation Streak: {streak_days} days
- Signal Strength: {signal_strength}

Context:
- Wallet Balance: {wallet_balance} BTC
- Historical behavior: {historical_behavior}
- Accumulation rate: {accumulation_rate} BTC/day
- Market context: {market_context}

Generate:
1. A headline (max 280 characters) about the whale activity
2. A 2-3 sentence summary explaining the accumulation pattern
3. List 2-3 pieces of supporting evidence
4. Explain potential market implications

Format your response as JSON:
{{
  "headline": "...",
  "summary": "...",
  "supporting_evidence": ["...", "...", "..."],
  "user_impact": "..."
}}
"""

    PREDICTIVE_SIGNAL_PROMPT = """Analyze this predictive signal and generate an insight:

Signal Data:
- Prediction Type: {prediction_type}
- Forecast Value: {forecast_value}
- Confidence Interval: [{ci_lower}, {ci_upper}]
- Forecast Horizon: {forecast_horizon}
- Model Version: {model_version}
- Signal Strength: {signal_strength}

Context:
- Current Value: {current_value}
- Predicted Change: {predicted_change}%
- Historical Accuracy: {historical_accuracy}%
- Model Confidence: {model_confidence}

Generate:
1. A headline (max 280 characters) about the prediction
2. A 2-3 sentence summary explaining the forecast and confidence
3. List 2-3 pieces of supporting evidence including confidence interval
4. Explain what users should watch for

Format your response as JSON:
{{
  "headline": "...",
  "summary": "...",
  "supporting_evidence": ["...", "...", "..."],
  "user_impact": "..."
}}
"""

    # Explainability prompt template
    EXPLAINABILITY_PROMPT = """Explain why this insight has a confidence score of {confidence:.2f}:

Insight:
- Headline: {headline}
- Signal Type: {signal_type}
- Signal Strength: {signal_strength}
- Data Quality: {data_quality}
- Historical Accuracy: {historical_accuracy}

Provide a clear explanation of:
1. How signal strength contributed to the confidence score
2. How data quality affected the score
3. How historical accuracy of similar insights influenced the score
4. Any factors that increased or decreased confidence

Format your response as JSON:
{{
  "explanation": "A clear 2-3 sentence explanation of the confidence score",
  "confidence_factors": {{
    "signal_strength": {signal_strength},
    "historical_accuracy": {historical_accuracy},
    "data_quality": {data_quality}
  }},
  "supporting_evidence": ["Factor 1 explanation", "Factor 2 explanation", "Factor 3 explanation"]
}}
"""

    @staticmethod
    def get_prompt_for_signal_type(signal_type: str) -> str:
        """Get the appropriate prompt template for a signal type"""
        prompts = {
            'mempool': PromptTemplates.MEMPOOL_PROMPT,
            'exchange': PromptTemplates.EXCHANGE_FLOW_PROMPT,
            'miner': PromptTemplates.MINER_TREASURY_PROMPT,
            'whale': PromptTemplates.WHALE_ACCUMULATION_PROMPT,
            'predictive': PromptTemplates.PREDICTIVE_SIGNAL_PROMPT,
        }
        return prompts.get(signal_type, PromptTemplates.MEMPOOL_PROMPT)

    @staticmethod
    def format_prompt(signal_type: str, signal_data: Dict[str, Any]) -> str:
        """Format a prompt with signal data"""
        template = PromptTemplates.get_prompt_for_signal_type(signal_type)
        try:
            return template.format(**signal_data)
        except KeyError as e:
            raise ValueError(f"Missing required field in signal data: {e}")

    @staticmethod
    def format_explainability_prompt(
        confidence: float,
        headline: str,
        signal_type: str,
        signal_strength: float,
        data_quality: float,
        historical_accuracy: float
    ) -> str:
        """Format explainability prompt with insight data"""
        return PromptTemplates.EXPLAINABILITY_PROMPT.format(
            confidence=confidence,
            headline=headline,
            signal_type=signal_type,
            signal_strength=signal_strength,
            data_quality=data_quality,
            historical_accuracy=historical_accuracy
        )
