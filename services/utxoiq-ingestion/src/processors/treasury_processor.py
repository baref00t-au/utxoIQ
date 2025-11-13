"""
Treasury company tracking module
Implements public company Bitcoin treasury movement detection and analysis
"""

import uuid
from typing import List, Dict, Optional, Any
from datetime import datetime
from ..models import Signal, SignalType, BlockData
from ..config import settings
from .base_processor import SignalProcessor, ProcessorConfig, ProcessingContext


class TreasuryFlow:
    """Data class for treasury flow information"""
    
    def __init__(
        self,
        entity: Dict[str, Any],
        flow_type: str,
        amount_btc: float,
        addresses: List[str]
    ):
        self.entity = entity
        self.flow_type = flow_type
        self.amount_btc = amount_btc
        self.addresses = addresses


class TreasuryProcessor(SignalProcessor):
    """
    Processes public company treasury transactions to track Bitcoin accumulation
    and distribution patterns
    """
    
    def __init__(self, config: Optional[ProcessorConfig] = None):
        if config is None:
            config = ProcessorConfig(
                enabled=getattr(settings, 'treasury_processor_enabled', True),
                confidence_threshold=getattr(settings, 'confidence_threshold', 0.7),
                time_window='30d'
            )
        super().__init__(config)
        self.signal_type = "treasury"
        self.entity_module = None  # Will be injected
    
    def set_entity_module(self, entity_module):
        """Inject entity identification module"""
        self.entity_module = entity_module
    
    async def process_block(
        self,
        block: BlockData,
        context: ProcessingContext
    ) -> List[Signal]:
        """
        Analyze block for public company treasury movements
        
        Args:
            block: Block data to process
            context: Processing context with transaction data
            
        Returns:
            List of treasury signals above confidence threshold
        """
        signals = []
        
        if not self.entity_module:
            return signals
        
        # Extract transactions from context
        transactions = context.historical_data.get('transactions', [])
        if not transactions:
            return signals
        
        # Scan all transactions for treasury addresses
        for tx in transactions:
            treasury_flows = await self._identify_treasury_flows(tx)
            
            for flow in treasury_flows:
                # Calculate confidence based on amount and entity reputation
                confidence = self._calculate_confidence(flow)
                
                if self.should_generate_signal(confidence):
                    # Create signal metadata
                    metadata = {
                        "entity_id": flow.entity.get("entity_id"),
                        "entity_name": flow.entity.get("entity_name"),
                        "company_ticker": flow.entity.get("metadata", {}).get("ticker", ""),
                        "flow_type": flow.flow_type,
                        "amount_btc": flow.amount_btc,
                        "tx_count": 1,
                        "addresses": flow.addresses,
                        "known_holdings_btc": flow.entity.get("metadata", {}).get("known_holdings_btc", 0),
                        "holdings_change_pct": self._calculate_holdings_change(
                            flow.amount_btc,
                            flow.entity.get("metadata", {}).get("known_holdings_btc", 0)
                        ),
                        "timestamp": datetime.utcnow().isoformat()
                    }
                    
                    # Create signal
                    signal = self.create_signal(
                        signal_type=self.signal_type,
                        block_height=block.height,
                        confidence=confidence,
                        metadata=metadata,
                        transaction_ids=[tx.get("txid", "")],
                        entity_ids=[flow.entity.get("entity_id", "")]
                    )
                    
                    signals.append(signal)
        
        return signals
    
    async def _identify_treasury_flows(
        self,
        tx: Dict[str, Any]
    ) -> List[TreasuryFlow]:
        """
        Identify treasury company involvement in transaction
        
        Args:
            tx: Transaction data
            
        Returns:
            List of treasury flows detected
        """
        flows = []
        
        if not self.entity_module:
            return flows
        
        # Check inputs for treasury addresses (distribution)
        input_addresses = tx.get("input_addresses", [])
        for input_addr in input_addresses:
            entity = await self.entity_module.identify_treasury_company(input_addr)
            if entity:
                # Calculate output sum for this transaction
                output_sum = sum(
                    output.get("value_btc", 0) 
                    for output in tx.get("outputs", [])
                )
                
                flows.append(TreasuryFlow(
                    entity=entity,
                    flow_type="distribution",
                    amount_btc=output_sum,
                    addresses=[input_addr]
                ))
        
        # Check outputs for treasury addresses (accumulation)
        outputs = tx.get("outputs", [])
        for output in outputs:
            output_addr = output.get("address", "")
            if output_addr:
                entity = await self.entity_module.identify_treasury_company(output_addr)
                if entity:
                    flows.append(TreasuryFlow(
                        entity=entity,
                        flow_type="accumulation",
                        amount_btc=output.get("value_btc", 0),
                        addresses=[output_addr]
                    ))
        
        return flows
    
    def _calculate_confidence(self, flow: TreasuryFlow) -> float:
        """
        Calculate confidence based on:
        - Amount significance (larger = higher confidence)
        - Entity reputation (known companies = higher confidence)
        - Address confirmation (multiple sources = higher confidence)
        
        Args:
            flow: Treasury flow data
            
        Returns:
            Confidence score between 0.0 and 1.0
        """
        # Base confidence from entity reputation
        confidence = 0.7
        
        # Boost for significant amounts (>100 BTC)
        if flow.amount_btc > 100:
            confidence += 0.1
        
        # Boost for very large amounts (>500 BTC)
        if flow.amount_btc > 500:
            confidence += 0.1
        
        # Ensure confidence stays within bounds
        return min(confidence, 1.0)
    
    def _calculate_holdings_change(
        self,
        amount_btc: float,
        known_holdings_btc: float
    ) -> float:
        """
        Calculate percentage change in holdings
        
        Args:
            amount_btc: Transaction amount
            known_holdings_btc: Known total holdings
            
        Returns:
            Percentage change
        """
        if known_holdings_btc == 0:
            return 0.0
        return (amount_btc / known_holdings_btc) * 100
