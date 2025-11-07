"""
Miner treasury tracking module
Implements daily balance change calculation and treasury delta computation
"""

import numpy as np
from typing import List, Dict, Optional
from datetime import datetime, timedelta
from ..models import Signal, SignalType, MinerTreasuryData
from ..config import settings


class MinerProcessor:
    """
    Processes miner treasury data to track balance changes and spending patterns
    """
    
    def __init__(self):
        self.significant_change_threshold = 10.0  # BTC
        self.historical_window = 144  # ~24 hours of blocks
        
    def calculate_daily_balance_change(
        self,
        current_data: MinerTreasuryData,
        previous_data: Optional[MinerTreasuryData] = None
    ) -> Dict[str, float]:
        """
        Calculate daily balance change for mining entity
        
        Args:
            current_data: Current treasury data
            previous_data: Previous day's treasury data
            
        Returns:
            Dictionary with balance change metrics
        """
        change_metrics = {
            "current_balance": current_data.balance_btc,
            "daily_change": current_data.daily_change_btc,
            "mining_rewards": current_data.mining_rewards_btc,
            "net_spending": 0.0,
            "change_percentage": 0.0
        }
        
        if previous_data:
            # Calculate net spending (rewards - actual change)
            expected_balance = (
                previous_data.balance_btc + current_data.mining_rewards_btc
            )
            actual_balance = current_data.balance_btc
            net_spending = expected_balance - actual_balance
            
            change_metrics["net_spending"] = net_spending
            
            # Calculate percentage change
            if previous_data.balance_btc > 0:
                change_pct = (
                    current_data.daily_change_btc / previous_data.balance_btc
                ) * 100
                change_metrics["change_percentage"] = change_pct
        
        return change_metrics
    
    def compute_treasury_delta(
        self,
        current_data: MinerTreasuryData,
        historical_data: Optional[List[MinerTreasuryData]] = None
    ) -> Dict[str, any]:
        """
        Compute treasury delta with historical comparison
        
        Args:
            current_data: Current treasury data
            historical_data: Historical treasury data for comparison
            
        Returns:
            Dictionary with delta analysis
        """
        delta_analysis = {
            "current_change": current_data.daily_change_btc,
            "is_significant": abs(current_data.daily_change_btc) > self.significant_change_threshold,
            "change_direction": "accumulating" if current_data.daily_change_btc > 0 else "spending",
            "historical_avg_change": 0.0,
            "deviation_from_avg": 0.0,
            "trend": "neutral"
        }
        
        if not historical_data or len(historical_data) < 7:
            return delta_analysis
        
        # Calculate historical average daily change
        historical_changes = [d.daily_change_btc for d in historical_data]
        avg_change = np.mean(historical_changes)
        std_change = np.std(historical_changes)
        
        delta_analysis["historical_avg_change"] = float(avg_change)
        delta_analysis["deviation_from_avg"] = float(
            current_data.daily_change_btc - avg_change
        )
        
        # Determine trend
        if len(historical_data) >= 7:
            recent_changes = [d.daily_change_btc for d in historical_data[-7:]]
            if all(c < 0 for c in recent_changes):
                delta_analysis["trend"] = "consistent_spending"
            elif all(c > 0 for c in recent_changes):
                delta_analysis["trend"] = "consistent_accumulation"
            elif sum(1 for c in recent_changes if c < 0) >= 5:
                delta_analysis["trend"] = "mostly_spending"
            elif sum(1 for c in recent_changes if c > 0) >= 5:
                delta_analysis["trend"] = "mostly_accumulation"
        
        return delta_analysis
    
    def analyze_spending_pattern(
        self,
        current_data: MinerTreasuryData,
        historical_data: List[MinerTreasuryData]
    ) -> Dict[str, any]:
        """
        Analyze miner spending patterns
        
        Args:
            current_data: Current treasury data
            historical_data: Historical treasury data
            
        Returns:
            Dictionary with spending pattern analysis
        """
        pattern = {
            "is_unusual": False,
            "pattern_type": None,
            "magnitude": 0.0,
            "frequency": 0
        }
        
        if not historical_data or len(historical_data) < 14:
            return pattern
        
        # Check for large single-day spending
        spending_events = [
            d.daily_change_btc 
            for d in historical_data 
            if d.daily_change_btc < -self.significant_change_threshold
        ]
        
        if current_data.daily_change_btc < -self.significant_change_threshold:
            pattern["is_unusual"] = True
            pattern["pattern_type"] = "large_spending"
            pattern["magnitude"] = abs(current_data.daily_change_btc)
            pattern["frequency"] = len(spending_events)
        
        # Check for unusual accumulation
        if current_data.daily_change_btc > self.significant_change_threshold * 2:
            pattern["is_unusual"] = True
            pattern["pattern_type"] = "large_accumulation"
            pattern["magnitude"] = current_data.daily_change_btc
        
        return pattern
    
    def calculate_confidence_score(
        self,
        current_data: MinerTreasuryData,
        delta_analysis: Dict[str, any],
        pattern: Dict[str, any]
    ) -> float:
        """
        Calculate confidence score for miner treasury signal
        
        Args:
            current_data: Current treasury data
            delta_analysis: Delta analysis results
            pattern: Spending pattern analysis
            
        Returns:
            Confidence score between 0 and 1
        """
        confidence = 0.5
        
        # Increase confidence for known mining entities
        if current_data.entity_name and current_data.entity_name != "unknown":
            confidence += 0.2
        
        # Increase confidence for significant changes
        if delta_analysis.get("is_significant"):
            confidence += 0.15
        
        # Increase confidence for unusual patterns
        if pattern.get("is_unusual"):
            confidence += 0.15
        
        # Increase confidence for consistent trends
        trend = delta_analysis.get("trend", "neutral")
        if trend in ["consistent_spending", "consistent_accumulation"]:
            confidence += 0.1
        
        # Increase confidence for large treasury balances
        if current_data.balance_btc > 1000:
            confidence += 0.1
        
        # Decrease confidence for very small changes
        if abs(current_data.daily_change_btc) < 1.0:
            confidence -= 0.2
        
        return max(0.0, min(1.0, confidence))
    
    def create_entity_attribution(
        self,
        current_data: MinerTreasuryData
    ) -> Dict[str, str]:
        """
        Create entity attribution for signal
        
        Args:
            current_data: Current treasury data
            
        Returns:
            Dictionary with entity information
        """
        return {
            "entity_id": current_data.entity_id,
            "entity_name": current_data.entity_name,
            "entity_type": "mining_pool"
        }
    
    def generate_miner_signal(
        self,
        current_data: MinerTreasuryData,
        historical_data: Optional[List[MinerTreasuryData]] = None
    ) -> Signal:
        """
        Generate miner treasury signal with entity attribution
        
        Args:
            current_data: Current miner treasury data
            historical_data: Historical treasury data for comparison
            
        Returns:
            Signal object with miner treasury analysis
        """
        # Calculate balance change
        previous_data = historical_data[-1] if historical_data else None
        change_metrics = self.calculate_daily_balance_change(
            current_data,
            previous_data
        )
        
        # Compute treasury delta
        delta_analysis = self.compute_treasury_delta(
            current_data,
            historical_data
        )
        
        # Analyze spending pattern
        pattern = {}
        if historical_data:
            pattern = self.analyze_spending_pattern(
                current_data,
                historical_data
            )
        
        # Calculate confidence
        confidence = self.calculate_confidence_score(
            current_data,
            delta_analysis,
            pattern
        )
        
        # Create entity attribution
        entity_info = self.create_entity_attribution(current_data)
        
        # Build signal data
        signal_data = {
            "entity": entity_info,
            "balance_btc": current_data.balance_btc,
            "daily_change_btc": current_data.daily_change_btc,
            "mining_rewards_btc": current_data.mining_rewards_btc,
            "change_metrics": change_metrics,
            "delta_analysis": delta_analysis,
            "spending_pattern": pattern,
            "timestamp": current_data.timestamp.isoformat()
        }
        
        return Signal(
            type=SignalType.MINER,
            strength=confidence,
            data=signal_data,
            block_height=current_data.block_height,
            transaction_ids=current_data.transaction_ids[:10],
            entity_ids=[current_data.entity_id],
            is_predictive=False
        )
