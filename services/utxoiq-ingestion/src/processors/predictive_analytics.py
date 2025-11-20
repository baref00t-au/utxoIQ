"""
Predictive analytics module
Implements forecasting models for fee prediction and liquidity pressure analysis
"""

import numpy as np
from typing import List, Dict, Optional, Tuple
from datetime import datetime, timedelta
from scipy import stats
from ..models import Signal, SignalType, PredictiveSignal, PredictiveSignalType, MempoolData, ExchangeFlowData, BlockData
from ..config import settings
from .base_processor import SignalProcessor, ProcessorConfig, ProcessingContext


class PredictiveAnalyticsModule(SignalProcessor):
    """
    Implements predictive models for blockchain metrics forecasting
    Generates fee forecast and liquidity pressure signals
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                enabled=getattr(settings, 'predictive_processor_enabled', True),
                confidence_threshold=0.5,  # Lower threshold for predictive signals
                time_window='24h'
            )
        super().__init__(config)
        self.signal_type = "predictive"
        self.model_version = settings.model_version
        self.fee_forecast_horizon = settings.fee_forecast_horizon
        self.liquidity_window_hours = settings.liquidity_pressure_window_hours
        self.min_confidence = 0.5  # Filter predictions with confidence < 0.5
    
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Process block and generate predictive signals
        
        Args:
            block: Block data to process
            context: Processing context with historical data
            
        Returns:
            List of predictive signals above confidence threshold
        """
        signals = []
        
        # Generate fee forecast signal if mempool data available
        mempool_data = context.historical_data.get('mempool_data')
        historical_mempool = context.historical_data.get('historical_mempool', [])
        
        if mempool_data and historical_mempool:
            fee_signal = self.generate_fee_forecast_signal(
                historical_mempool,
                mempool_data
            )
            # Filter by minimum confidence (0.5)
            if fee_signal and fee_signal.strength >= self.min_confidence:
                signals.append(fee_signal)
        
        # Generate liquidity pressure signal if exchange flow data available
        exchange_flows = context.historical_data.get('historical_exchange_flows', [])
        current_flow = context.historical_data.get('current_exchange_flow')
        
        if exchange_flows and current_flow:
            liquidity_signal = self.generate_liquidity_pressure_signal(
                exchange_flows,
                current_flow
            )
            # Filter by minimum confidence (0.5)
            if liquidity_signal and liquidity_signal.strength >= self.min_confidence:
                signals.append(liquidity_signal)
        
        return signals
        
    def forecast_next_block_fees(
        self,
        historical_mempool: List[MempoolData],
        current_mempool: MempoolData
    ) -> Dict[str, any]:
        """
        Forecast next block fee rates using temporal models with historical data
        
        Args:
            historical_mempool: Historical mempool snapshots
            current_mempool: Current mempool state
            
        Returns:
            Dictionary with fee forecast and confidence interval
        """
        if not historical_mempool or len(historical_mempool) < 10:
            # Insufficient data for prediction
            return {
                "prediction": current_mempool.avg_fee_rate,
                "confidence_interval": (
                    current_mempool.avg_fee_rate * 0.8,
                    current_mempool.avg_fee_rate * 1.2
                ),
                "model_confidence": 0.3,
                "method": "fallback"
            }
        
        # Extract historical fee rates
        historical_fees = [m.avg_fee_rate for m in historical_mempool]
        
        # Simple exponential smoothing for short-term forecast
        alpha = 0.3  # Smoothing parameter
        forecast = self._exponential_smoothing(
            historical_fees,
            alpha
        )
        
        # Calculate prediction confidence interval using historical variance
        std_dev = np.std(historical_fees)
        confidence_interval = (
            max(1.0, forecast - 1.96 * std_dev),  # 95% CI lower bound
            forecast + 1.96 * std_dev  # 95% CI upper bound
        )
        
        # Calculate model confidence based on data quality
        model_confidence = self._calculate_forecast_confidence(
            historical_mempool,
            current_mempool
        )
        
        return {
            "prediction": float(forecast),
            "confidence_interval": confidence_interval,
            "model_confidence": model_confidence,
            "method": "exponential_smoothing",
            "historical_mean": float(np.mean(historical_fees)),
            "historical_std": float(std_dev)
        }
    
    def _exponential_smoothing(
        self,
        data: List[float],
        alpha: float
    ) -> float:
        """
        Apply exponential smoothing for time series forecasting
        
        Args:
            data: Historical data points
            alpha: Smoothing parameter (0-1)
            
        Returns:
            Forecasted value
        """
        if not data:
            return 0.0
        
        smoothed = data[0]
        for value in data[1:]:
            smoothed = alpha * value + (1 - alpha) * smoothed
        
        # Forecast next value
        return smoothed
    
    def _calculate_forecast_confidence(
        self,
        historical_mempool: List[MempoolData],
        current_mempool: MempoolData
    ) -> float:
        """
        Calculate confidence score for fee forecast
        
        Args:
            historical_mempool: Historical mempool data
            current_mempool: Current mempool state
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5
        
        # Increase confidence with more historical data
        if len(historical_mempool) >= 144:  # 24 hours
            confidence += 0.2
        elif len(historical_mempool) >= 72:  # 12 hours
            confidence += 0.1
        
        # Increase confidence for stable conditions
        recent_fees = [m.avg_fee_rate for m in historical_mempool[-10:]]
        if recent_fees:
            cv = np.std(recent_fees) / np.mean(recent_fees) if np.mean(recent_fees) > 0 else 1.0
            if cv < 0.2:  # Low coefficient of variation
                confidence += 0.2
            elif cv < 0.5:
                confidence += 0.1
        
        # Decrease confidence for unusual current conditions
        if current_mempool.transaction_count < 500:
            confidence -= 0.1
        
        return max(0.0, min(1.0, confidence))
    
    def compute_liquidity_pressure_index(
        self,
        exchange_flows: List[ExchangeFlowData],
        current_flow: ExchangeFlowData
    ) -> Dict[str, any]:
        """
        Compute Exchange Liquidity Pressure Index based on flow pattern analysis
        
        Args:
            exchange_flows: Historical exchange flow data
            current_flow: Current exchange flow
            
        Returns:
            Dictionary with liquidity pressure index and analysis
        """
        if not exchange_flows or len(exchange_flows) < 10:
            return {
                "pressure_index": 0.5,
                "pressure_level": "neutral",
                "confidence": 0.3,
                "method": "fallback"
            }
        
        # Calculate net flow metrics
        historical_net_flows = [f.net_flow_btc for f in exchange_flows]
        current_net_flow = current_flow.net_flow_btc
        
        # Calculate pressure index (0-1 scale)
        # Positive net flow (inflow) = selling pressure
        # Negative net flow (outflow) = buying pressure
        mean_flow = np.mean(historical_net_flows)
        std_flow = np.std(historical_net_flows)
        
        if std_flow > 0:
            z_score = (current_net_flow - mean_flow) / std_flow
            # Normalize z-score to 0-1 scale
            pressure_index = 0.5 + (z_score / 6.0)  # ±3 std devs
            pressure_index = max(0.0, min(1.0, pressure_index))
        else:
            pressure_index = 0.5
        
        # Determine pressure level
        if pressure_index >= 0.7:
            pressure_level = "high_selling_pressure"
        elif pressure_index >= 0.6:
            pressure_level = "moderate_selling_pressure"
        elif pressure_index <= 0.3:
            pressure_level = "high_buying_pressure"
        elif pressure_index <= 0.4:
            pressure_level = "moderate_buying_pressure"
        else:
            pressure_level = "neutral"
        
        # Calculate confidence
        confidence = self._calculate_liquidity_confidence(
            exchange_flows,
            current_flow
        )
        
        return {
            "pressure_index": float(pressure_index),
            "pressure_level": pressure_level,
            "confidence": confidence,
            "method": "z_score_normalization",
            "net_flow_btc": current_net_flow,
            "historical_mean_flow": float(mean_flow),
            "z_score": float(z_score) if std_flow > 0 else 0.0
        }
    
    def _calculate_liquidity_confidence(
        self,
        exchange_flows: List[ExchangeFlowData],
        current_flow: ExchangeFlowData
    ) -> float:
        """
        Calculate confidence for liquidity pressure index
        
        Args:
            exchange_flows: Historical exchange flows
            current_flow: Current exchange flow
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5
        
        # Increase confidence with more data
        if len(exchange_flows) >= 144:  # 24 hours
            confidence += 0.2
        elif len(exchange_flows) >= 72:
            confidence += 0.1
        
        # Increase confidence for known exchanges
        if current_flow.entity_name and current_flow.entity_name != "unknown":
            confidence += 0.15
        
        # Increase confidence for significant volume
        if current_flow.inflow_btc + current_flow.outflow_btc > 100:
            confidence += 0.15
        
        return max(0.0, min(1.0, confidence))
    
    def track_prediction_accuracy(
        self,
        prediction: float,
        actual: float,
        prediction_type: str
    ) -> Dict[str, float]:
        """
        Track prediction accuracy for model adjustment
        
        Args:
            prediction: Predicted value
            actual: Actual observed value
            prediction_type: Type of prediction
            
        Returns:
            Dictionary with accuracy metrics
        """
        # Calculate error metrics
        absolute_error = abs(prediction - actual)
        percentage_error = (
            (absolute_error / actual * 100) if actual != 0 else 0.0
        )
        
        # Calculate accuracy score (inverse of percentage error)
        accuracy_score = max(0.0, 1.0 - (percentage_error / 100.0))
        
        return {
            "prediction": prediction,
            "actual": actual,
            "absolute_error": absolute_error,
            "percentage_error": percentage_error,
            "accuracy_score": accuracy_score,
            "prediction_type": prediction_type,
            "timestamp": datetime.utcnow().isoformat()
        }
    
    def generate_fee_forecast_signal(
        self,
        historical_mempool: List[MempoolData],
        current_mempool: MempoolData
    ) -> Optional[Signal]:
        """
        Generate predictive signal for next block fee forecast
        
        Args:
            historical_mempool: Historical mempool data
            current_mempool: Current mempool state
            
        Returns:
            Signal object with fee forecast, or None if confidence < 0.5
        """
        # Generate forecast
        forecast = self.forecast_next_block_fees(
            historical_mempool,
            current_mempool
        )
        
        # Filter predictions with confidence < 0.5 (Requirement 10.6)
        if forecast["model_confidence"] < self.min_confidence:
            return None
        
        # Build signal metadata with required fields (Requirement 10.3, 10.4)
        signal_data = {
            "signal_type": "predictive",
            "prediction_type": "fee_forecast",
            "predicted_value": forecast["prediction"],
            "confidence_interval": forecast["confidence_interval"],
            "forecast_horizon": self.fee_forecast_horizon,
            "model_version": self.model_version,
            "current_value": current_mempool.avg_fee_rate,
            "historical_mean": forecast.get("historical_mean", 0.0),
            "historical_std": forecast.get("historical_std", 0.0),
            "method": forecast["method"],
            "timestamp": current_mempool.timestamp.isoformat()
        }
        
        return Signal(
            type=SignalType.PREDICTIVE,
            strength=forecast["model_confidence"],
            data=signal_data,
            block_height=current_mempool.block_height,
            transaction_ids=[],
            entity_ids=[],
            is_predictive=True,
            prediction_confidence_interval=forecast["confidence_interval"]
        )
    
    def generate_liquidity_pressure_signal(
        self,
        exchange_flows: List[ExchangeFlowData],
        current_flow: ExchangeFlowData
    ) -> Optional[Signal]:
        """
        Generate predictive signal for exchange liquidity pressure
        
        Args:
            exchange_flows: Historical exchange flow data
            current_flow: Current exchange flow
            
        Returns:
            Signal object with liquidity pressure analysis, or None if confidence < 0.5
        """
        # Compute liquidity pressure
        pressure = self.compute_liquidity_pressure_index(
            exchange_flows,
            current_flow
        )
        
        # Filter predictions with confidence < 0.5 (Requirement 10.6)
        if pressure["confidence"] < self.min_confidence:
            return None
        
        # Calculate confidence interval
        confidence_interval = (
            max(0.0, pressure["pressure_index"] - 0.1),
            min(1.0, pressure["pressure_index"] + 0.1)
        )
        
        # Build signal metadata with required fields (Requirement 10.3, 10.4)
        signal_data = {
            "signal_type": "predictive",
            "prediction_type": "liquidity_pressure",
            "predicted_value": pressure["pressure_index"],
            "confidence_interval": confidence_interval,
            "forecast_horizon": f"{self.liquidity_window_hours}h",
            "model_version": self.model_version,
            "pressure_level": pressure["pressure_level"],
            "net_flow_btc": pressure["net_flow_btc"],
            "historical_mean_flow": pressure["historical_mean_flow"],
            "z_score": pressure.get("z_score", 0.0),
            "method": pressure["method"],
            "entity_id": current_flow.entity_id,
            "entity_name": current_flow.entity_name,
            "timestamp": current_flow.timestamp.isoformat()
        }
        
        return Signal(
            type=SignalType.PREDICTIVE,
            strength=pressure["confidence"],
            data=signal_data,
            block_height=current_flow.block_height,
            transaction_ids=current_flow.transaction_ids[:10],
            entity_ids=[current_flow.entity_id],
            is_predictive=True,
            prediction_confidence_interval=confidence_interval
        )
