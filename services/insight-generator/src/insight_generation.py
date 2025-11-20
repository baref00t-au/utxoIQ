"""
Insight Generation Module for insight-generator service.

This module orchestrates the complete insight generation process:
1. Selects appropriate prompt template based on signal type
2. Invokes AI provider with formatted prompt
3. Parses and validates AI response
4. Extracts blockchain evidence from signal metadata
5. Creates complete insight records ready for persistence

Requirements: 3.3, 3.4, 4.2
"""

import uuid
import logging
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from datetime import datetime

from .ai_provider import AIProvider, Signal, InsightContent, AIProviderError
from .prompts import (
    mempool_prompt,
    exchange_prompt,
    miner_prompt,
    whale_prompt,
    treasury_prompt,
    predictive_prompt
)


logger = logging.getLogger(__name__)


@dataclass
class Evidence:
    """Blockchain evidence for an insight"""
    block_heights: List[int]
    transaction_ids: List[str]


@dataclass
class Insight:
    """Complete insight record ready for persistence"""
    insight_id: str
    signal_id: str
    category: str  # mempool|exchange|miner|whale|treasury|predictive
    headline: str
    summary: str
    confidence: float
    evidence: Evidence
    chart_url: Optional[str] = None
    created_at: Optional[datetime] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert insight to dictionary for BigQuery insertion"""
        return {
            "insight_id": self.insight_id,
            "signal_id": self.signal_id,
            "category": self.category,
            "headline": self.headline,
            "summary": self.summary,
            "confidence": self.confidence,
            "evidence": {
                "block_heights": self.evidence.block_heights,
                "transaction_ids": self.evidence.transaction_ids
            },
            "chart_url": self.chart_url,
            "created_at": self.created_at or datetime.utcnow()
        }


class InsightGenerationModule:
    """
    Main insight generation module that orchestrates the complete process.
    
    Responsibilities:
    - Select appropriate prompt template based on signal_type
    - Invoke AI provider with formatted prompt
    - Parse AI response and validate JSON structure
    - Extract blockchain evidence from signal metadata
    - Create complete insight records
    
    Requirements: 3.3, 3.4, 4.2
    """
    
    # Map signal types to prompt templates
    PROMPT_TEMPLATES = {
        "mempool": mempool_prompt.MEMPOOL_TEMPLATE,
        "exchange": exchange_prompt.EXCHANGE_TEMPLATE,
        "miner": miner_prompt.MINER_TEMPLATE,
        "whale": whale_prompt.WHALE_TEMPLATE,
        "treasury": treasury_prompt.TREASURY_TEMPLATE,
        "predictive": predictive_prompt.PREDICTIVE_TEMPLATE
    }
    
    def __init__(self, ai_provider: AIProvider):
        """
        Initialize Insight Generation Module.
        
        Args:
            ai_provider: Configured AI provider instance (Vertex AI, OpenAI, etc.)
        """
        self.ai_provider = ai_provider
        logger.info(
            f"InsightGenerationModule initialized with provider: "
            f"{ai_provider.__class__.__name__}"
        )
    
    async def generate_insight(
        self,
        signal: Dict[str, Any]
    ) -> Optional[Insight]:
        """
        Generate a complete insight from a signal.
        
        This is the main entry point for insight generation. It:
        1. Validates signal data
        2. Selects appropriate prompt template
        3. Invokes AI provider
        4. Parses response
        5. Extracts evidence
        6. Creates insight record
        
        Args:
            signal: Signal dictionary from BigQuery with fields:
                - signal_id: str
                - signal_type: str
                - block_height: int
                - confidence: float
                - metadata: dict
                - created_at: datetime
        
        Returns:
            Insight object ready for persistence, or None if generation fails
            
        Requirements: 3.3, 3.4
        """
        try:
            signal_id = signal.get("signal_id")
            signal_type = signal.get("signal_type")
            
            logger.info(
                f"Generating insight for signal {signal_id} (type: {signal_type})"
            )
            
            # Step 1: Validate signal data
            if not self._validate_signal(signal):
                logger.error(
                    f"Invalid signal data for signal {signal_id}",
                    extra={"signal": signal}
                )
                return None
            
            # Step 2: Select prompt template based on signal_type
            prompt_template = self._select_prompt_template(signal_type)
            
            if not prompt_template:
                logger.error(
                    f"No prompt template found for signal type: {signal_type}",
                    extra={"signal_id": signal_id}
                )
                return None
            
            # Step 3: Create Signal object for AI provider
            signal_obj = Signal(
                signal_id=signal_id,
                signal_type=signal_type,
                block_height=signal.get("block_height"),
                confidence=signal.get("confidence"),
                metadata=signal.get("metadata", {})
            )
            
            # Step 4: Invoke AI provider with formatted prompt
            try:
                ai_content = await self.ai_provider.generate_insight(
                    signal_obj,
                    prompt_template
                )
            except AIProviderError as e:
                logger.error(
                    f"AI provider failed for signal {signal_id}: {e}",
                    extra={"signal_id": signal_id, "error": str(e)}
                )
                return None
            
            # Step 5: Validate AI response
            if not self._validate_ai_content(ai_content):
                logger.error(
                    f"Invalid AI content for signal {signal_id}",
                    extra={"signal_id": signal_id}
                )
                return None
            
            # Step 6: Extract blockchain evidence from signal metadata
            evidence = self._extract_evidence(signal)
            
            # Step 7: Create insight record
            insight = Insight(
                insight_id=str(uuid.uuid4()),
                signal_id=signal_id,
                category=signal_type,
                headline=ai_content.headline,
                summary=ai_content.summary,
                confidence=signal.get("confidence"),
                evidence=evidence,
                chart_url=None,  # Populated later by chart-renderer
                created_at=datetime.utcnow()
            )
            
            logger.info(
                f"Successfully generated insight {insight.insight_id} "
                f"for signal {signal_id}",
                extra={
                    "insight_id": insight.insight_id,
                    "signal_id": signal_id,
                    "category": signal_type
                }
            )
            
            return insight
            
        except Exception as e:
            logger.error(
                f"Unexpected error generating insight for signal "
                f"{signal.get('signal_id')}: {e}",
                extra={"signal": signal, "error": str(e)}
            )
            return None
    
    def _validate_signal(self, signal: Dict[str, Any]) -> bool:
        """
        Validate that signal has all required fields.
        
        Args:
            signal: Signal dictionary
            
        Returns:
            True if valid, False otherwise
        """
        required_fields = [
            "signal_id",
            "signal_type",
            "block_height",
            "confidence",
            "metadata"
        ]
        
        for field in required_fields:
            if field not in signal:
                logger.error(f"Missing required field: {field}")
                return False
        
        # Validate signal_type is supported
        if signal["signal_type"] not in self.PROMPT_TEMPLATES:
            logger.error(
                f"Unsupported signal type: {signal['signal_type']}"
            )
            return False
        
        return True
    
    def _select_prompt_template(self, signal_type: str) -> Optional[str]:
        """
        Select appropriate prompt template based on signal type.
        
        Args:
            signal_type: Type of signal (mempool, exchange, miner, etc.)
            
        Returns:
            Prompt template string, or None if not found
            
        Requirements: 3.3
        """
        template = self.PROMPT_TEMPLATES.get(signal_type)
        
        if template:
            logger.debug(f"Selected {signal_type} prompt template")
        else:
            logger.warning(f"No template found for signal type: {signal_type}")
        
        return template
    
    def _validate_ai_content(self, content: InsightContent) -> bool:
        """
        Validate AI-generated content.
        
        Args:
            content: InsightContent from AI provider
            
        Returns:
            True if valid, False otherwise
            
        Requirements: 3.4
        """
        # Check headline length (max 80 chars)
        if not content.headline or len(content.headline) > 80:
            logger.error(
                f"Invalid headline length: {len(content.headline) if content.headline else 0}"
            )
            return False
        
        # Check summary exists and is reasonable length
        if not content.summary or len(content.summary) < 10:
            logger.error("Summary too short or missing")
            return False
        
        # Check confidence explanation exists
        if not content.confidence_explanation:
            logger.error("Confidence explanation missing")
            return False
        
        return True
    
    def _extract_evidence(self, signal: Dict[str, Any]) -> Evidence:
        """
        Extract blockchain evidence from signal metadata.
        
        Extracts:
        - Block heights: Always includes the signal's block_height
        - Transaction IDs: Extracted from metadata if present
        
        Args:
            signal: Signal dictionary with metadata
            
        Returns:
            Evidence object with block heights and transaction IDs
            
        Requirements: 4.2
        """
        metadata = signal.get("metadata", {})
        block_height = signal.get("block_height")
        
        # Always include the signal's block height
        block_heights = [block_height] if block_height else []
        
        # Extract transaction IDs from metadata
        # Different signal types store tx IDs in different fields
        transaction_ids = []
        
        # Check common metadata fields for transaction IDs
        possible_tx_fields = [
            "tx_ids",
            "transaction_ids",
            "txids",
            "transactions"
        ]
        
        for field in possible_tx_fields:
            if field in metadata:
                value = metadata[field]
                if isinstance(value, list):
                    transaction_ids.extend(value)
                elif isinstance(value, str):
                    transaction_ids.append(value)
        
        # For exchange/whale/treasury signals, may have addresses instead
        # Log if we found addresses but no tx IDs
        if not transaction_ids and "addresses" in metadata:
            logger.debug(
                f"Signal {signal.get('signal_id')} has addresses but no tx IDs",
                extra={"signal_id": signal.get("signal_id")}
            )
        
        # Remove duplicates and ensure all are strings
        transaction_ids = list(set(str(tx_id) for tx_id in transaction_ids))
        
        evidence = Evidence(
            block_heights=block_heights,
            transaction_ids=transaction_ids
        )
        
        logger.debug(
            f"Extracted evidence: {len(block_heights)} blocks, "
            f"{len(transaction_ids)} transactions",
            extra={"signal_id": signal.get("signal_id")}
        )
        
        return evidence
    
    async def generate_insights_batch(
        self,
        signals: List[Dict[str, Any]]
    ) -> List[Insight]:
        """
        Generate insights for multiple signals in batch.
        
        Processes signals sequentially but provides a convenient
        batch interface for the polling loop.
        
        Args:
            signals: List of signal dictionaries
            
        Returns:
            List of successfully generated insights
        """
        insights = []
        
        logger.info(f"Generating insights for {len(signals)} signals")
        
        for signal in signals:
            insight = await self.generate_insight(signal)
            if insight:
                insights.append(insight)
        
        logger.info(
            f"Successfully generated {len(insights)} insights "
            f"from {len(signals)} signals"
        )
        
        return insights
