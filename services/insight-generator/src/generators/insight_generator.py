"""
Main InsightGenerator class
Integrates Vertex AI, prompt templates, confidence scoring, and explainability
"""

import json
import uuid
from typing import Dict, Any, Optional, List
from datetime import datetime

from .confidence_scorer import ConfidenceScorer, ConfidenceScore
from .explainability_generator import ExplainabilityGenerator, ExplainabilitySummary
from .citation_formatter import CitationFormatter, Citation
from .headline_generator import HeadlineGenerator
from ..prompts.templates import PromptTemplates


class Insight:
    """Insight model"""
    def __init__(
        self,
        id: str,
        signal_type: str,
        headline: str,
        summary: str,
        confidence: float,
        timestamp: datetime,
        block_height: int,
        evidence: List[Citation],
        chart_url: Optional[str] = None,
        tags: Optional[List[str]] = None,
        explainability: Optional[ExplainabilitySummary] = None,
        accuracy_rating: Optional[float] = None,
        is_predictive: bool = False
    ):
        self.id = id
        self.signal_type = signal_type
        self.headline = headline
        self.summary = summary
        self.confidence = confidence
        self.timestamp = timestamp
        self.block_height = block_height
        self.evidence = evidence
        self.chart_url = chart_url
        self.tags = tags or []
        self.explainability = explainability
        self.accuracy_rating = accuracy_rating
        self.is_predictive = is_predictive
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary"""
        return {
            'id': self.id,
            'signal_type': self.signal_type,
            'headline': self.headline,
            'summary': self.summary,
            'confidence': self.confidence,
            'timestamp': self.timestamp.isoformat(),
            'block_height': self.block_height,
            'evidence': [e.dict() for e in self.evidence],
            'chart_url': self.chart_url,
            'tags': self.tags,
            'explainability': self.explainability.to_dict() if self.explainability else None,
            'accuracy_rating': self.accuracy_rating,
            'is_predictive': self.is_predictive
        }


class InsightGenerator:
    """Main insight generator integrating all components"""
    
    def __init__(self, vertex_ai_client=None, model_version: str = "1.0.0"):
        """
        Initialize insight generator
        
        Args:
            vertex_ai_client: Vertex AI client (optional for testing)
            model_version: Model version string
        """
        self.vertex_ai_client = vertex_ai_client
        self.model_version = model_version
        self.confidence_scorer = ConfidenceScorer()
        self.explainability_generator = ExplainabilityGenerator()
        self.citation_formatter = CitationFormatter()
        self.headline_generator = HeadlineGenerator()
        self.prompt_templates = PromptTemplates()
    
    def generate_insight(
        self,
        signal_data: Dict[str, Any],
        signal_type: str,
        chart_url: Optional[str] = None
    ) -> Optional[Insight]:
        """
        Generate a complete insight from signal data
        
        Args:
            signal_data: Raw signal data
            signal_type: Type of signal
            chart_url: Optional chart URL
            
        Returns:
            Insight object or None if generation fails
        """
        try:
            # Step 1: Check for quiet mode
            should_quiet, quiet_reason = self.confidence_scorer.detect_quiet_mode(
                signal_data, signal_type
            )
            
            if should_quiet:
                print(f"Entering quiet mode: {quiet_reason}")
                return None
            
            # Step 2: Calculate confidence score
            signal_strength = self.confidence_scorer.calculate_signal_strength(
                signal_data, signal_type
            )
            data_quality = self.confidence_scorer.calculate_data_quality(signal_data)
            historical_accuracy = self.confidence_scorer.get_historical_accuracy(
                signal_type, self.model_version
            )
            is_anomaly = signal_data.get('is_anomaly', False)
            
            confidence_score = self.confidence_scorer.calculate_confidence(
                signal_strength=signal_strength,
                historical_accuracy=historical_accuracy,
                data_quality=data_quality,
                is_anomaly=is_anomaly
            )
            
            # Step 3: Check if should publish
            if not confidence_score.should_publish:
                print(f"Confidence {confidence_score.score:.2f} below publication threshold")
                return None
            
            # Step 4: Generate insight content using AI
            ai_response = self._generate_ai_content(signal_data, signal_type)
            
            if not ai_response:
                print("AI content generation failed")
                return None
            
            # Step 5: Extract and validate headline
            headline = self._extract_headline(ai_response, signal_type, signal_data)
            
            # Step 6: Extract summary
            summary = self._extract_summary(ai_response)
            
            # Step 7: Create citations
            citations = self.citation_formatter.create_citations_from_signal(signal_data)
            
            # Step 8: Generate explainability
            explainability = self.explainability_generator.generate_explainability(
                confidence_score, signal_type, signal_data
            )
            
            # Step 9: Extract tags
            tags = self._extract_tags(signal_type, signal_data)
            
            # Step 10: Create insight object
            insight = Insight(
                id=str(uuid.uuid4()),
                signal_type=signal_type,
                headline=headline,
                summary=summary,
                confidence=confidence_score.score,
                timestamp=datetime.now(),
                block_height=signal_data.get('block_height', 0),
                evidence=citations,
                chart_url=chart_url,
                tags=tags,
                explainability=explainability,
                is_predictive=signal_data.get('is_predictive', False)
            )
            
            return insight
            
        except Exception as e:
            print(f"Error generating insight: {e}")
            return None
    
    def _generate_ai_content(
        self,
        signal_data: Dict[str, Any],
        signal_type: str
    ) -> Optional[Dict[str, Any]]:
        """Generate content using Vertex AI"""
        try:
            # Format prompt
            prompt = self.prompt_templates.format_prompt(signal_type, signal_data)
            
            if not self.vertex_ai_client:
                # Mock response for testing
                return {
                    'headline': self.headline_generator.generate_fallback_headline(
                        signal_type, signal_data.get('block_height', 0)
                    ),
                    'summary': f"Significant {signal_type} activity detected on the Bitcoin blockchain.",
                    'supporting_evidence': [
                        f"Signal strength: {signal_data.get('signal_strength', 0):.2f}",
                        f"Block height: {signal_data.get('block_height', 0)}"
                    ],
                    'user_impact': "Traders should monitor this development closely."
                }
            
            # Call Vertex AI
            response = self.vertex_ai_client.generate_content(
                prompt,
                system_instruction=self.prompt_templates.SYSTEM_PROMPT
            )
            
            # Parse JSON response
            response_text = response.text
            ai_content = json.loads(response_text)
            
            return ai_content
            
        except Exception as e:
            print(f"Error generating AI content: {e}")
            return None
    
    def _extract_headline(
        self,
        ai_response: Dict[str, Any],
        signal_type: str,
        signal_data: Dict[str, Any]
    ) -> str:
        """Extract and validate headline from AI response"""
        headline = ai_response.get('headline', '')
        
        # Clean and validate
        headline = self.headline_generator.clean_headline(headline)
        
        if not self.headline_generator.validate_headline(headline):
            # Use fallback
            headline = self.headline_generator.generate_fallback_headline(
                signal_type, signal_data.get('block_height', 0)
            )
        
        # Truncate if needed
        headline = self.headline_generator.truncate_headline(headline)
        
        return headline
    
    def _extract_summary(self, ai_response: Dict[str, Any]) -> str:
        """Extract summary from AI response"""
        summary = ai_response.get('summary', '')
        
        if not summary:
            summary = "Blockchain activity detected. See evidence for details."
        
        return summary.strip()
    
    def _extract_tags(self, signal_type: str, signal_data: Dict[str, Any]) -> List[str]:
        """Extract relevant tags for the insight"""
        tags = [signal_type]
        
        # Add confidence level tag
        if signal_data.get('signal_strength', 0) >= 0.8:
            tags.append('high-confidence')
        
        # Add anomaly tag
        if signal_data.get('is_anomaly', False):
            tags.append('anomaly')
        
        # Add predictive tag
        if signal_data.get('is_predictive', False):
            tags.append('predictive')
        
        # Add signal-specific tags
        if signal_type == 'mempool':
            if signal_data.get('change_24h', 0) > 50:
                tags.append('high-volatility')
        elif signal_type == 'exchange':
            if signal_data.get('exchange_name'):
                tags.append(f"exchange-{signal_data['exchange_name'].lower()}")
        elif signal_type == 'miner':
            if signal_data.get('trend') == 'accumulating':
                tags.append('accumulation')
            elif signal_data.get('trend') == 'distributing':
                tags.append('distribution')
        elif signal_type == 'whale':
            if signal_data.get('streak_days', 0) >= 7:
                tags.append('long-streak')
        
        return tags
    
    def generate_explainability_for_existing_insight(
        self,
        insight: Insight,
        signal_data: Dict[str, Any]
    ) -> ExplainabilitySummary:
        """Generate explainability for an existing insight"""
        # Reconstruct confidence score
        signal_strength = self.confidence_scorer.calculate_signal_strength(
            signal_data, insight.signal_type
        )
        data_quality = self.confidence_scorer.calculate_data_quality(signal_data)
        historical_accuracy = self.confidence_scorer.get_historical_accuracy(
            insight.signal_type, self.model_version
        )
        
        confidence_score = self.confidence_scorer.calculate_confidence(
            signal_strength=signal_strength,
            historical_accuracy=historical_accuracy,
            data_quality=data_quality
        )
        
        return self.explainability_generator.generate_explainability(
            confidence_score, insight.signal_type, signal_data
        )
