"""
Predictive signal prompt template for AI insight generation
"""

PREDICTIVE_TEMPLATE = """You are a Bitcoin blockchain analyst. Generate a forward-looking insight about this predictive signal.

Signal Data:
- Prediction Type: {prediction_type}
- Predicted Value: {predicted_value}
- Confidence Interval: {confidence_interval}
- Forecast Horizon: {forecast_horizon}
- Current Value: {current_value}

Provide:
1. Headline (max 80 chars) - Emphasize the forward-looking nature of the prediction
2. Summary (2-3 sentences) - Explain what to expect and why based on the forecast
3. Confidence Explanation - Explain model reliability and data quality

Format as JSON:
{{
  "headline": "...",
  "summary": "...",
  "confidence_explanation": "..."
}}
"""
