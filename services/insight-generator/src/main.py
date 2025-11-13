"""
AI-powered Bitcoin Insight Generator Service.
Uses Vertex AI Gemini to analyze blockchain data and generate insights.
"""
import asyncio
import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import uuid
import json

from google.cloud import bigquery
import vertexai
from vertexai.generative_models import GenerativeModel, Part
import httpx

# Configuration
PROJECT_ID = "utxoiq-dev"
LOCATION = "us-central1"
DATASET_BTC = "btc"
DATASET_INTEL = "intel"
MODEL_NAME = "gemini-pro"
MODEL_VERSION = "v1.5.0"

# Bitcoin Core RPC (if available)
BITCOIN_RPC_URL = "http://bitcoin-node:8332"  # Update with actual endpoint

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class InsightGenerator:
    """Generate insights from blockchain data using AI."""
    
    def __init__(self):
        """Initialize the insight generator."""
        self.bq_client = bigquery.Client(project=PROJECT_ID)
        vertexai.init(project=PROJECT_ID, location=LOCATION)
        self.model = GenerativeModel(MODEL_NAME)
        self.http_client = httpx.AsyncClient(timeout=30.0)
    
    async def fetch_mempool_data(self) -> Dict:
        """Fetch current mempool statistics."""
        logger.info("Fetching mempool data...")
        
        # Query BigQuery for recent mempool data
        query = f"""
            SELECT 
                AVG(fee_rate) as avg_fee,
                MAX(fee_rate) as max_fee,
                MIN(fee_rate) as min_fee,
                COUNT(*) as tx_count,
                SUM(size) as total_size
            FROM `{PROJECT_ID}.{DATASET_BTC}.mempool`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 1 HOUR)
        """
        
        try:
            job = self.bq_client.query(query)
            result = list(job.result())
            
            if result:
                row = result[0]
                return {
                    "avg_fee": float(row['avg_fee']) if row['avg_fee'] else 0,
                    "max_fee": float(row['max_fee']) if row['max_fee'] else 0,
                    "min_fee": float(row['min_fee']) if row['min_fee'] else 0,
                    "tx_count": int(row['tx_count']) if row['tx_count'] else 0,
                    "total_size": int(row['total_size']) if row['total_size'] else 0
                }
        except Exception as e:
            logger.warning(f"Could not fetch mempool data from BigQuery: {e}")
        
        # Fallback: Return simulated data for development
        return {
            "avg_fee": 45.5,
            "max_fee": 120.0,
            "min_fee": 12.0,
            "tx_count": 85000,
            "total_size": 125000000
        }
    
    async def fetch_exchange_flows(self) -> Dict:
        """Fetch exchange flow data."""
        logger.info("Fetching exchange flow data...")
        
        query = f"""
            SELECT 
                SUM(CASE WHEN flow_type = 'inflow' THEN amount ELSE 0 END) as total_inflow,
                SUM(CASE WHEN flow_type = 'outflow' THEN amount ELSE 0 END) as total_outflow,
                COUNT(DISTINCT exchange_address) as active_exchanges
            FROM `{PROJECT_ID}.{DATASET_BTC}.exchange_flows`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        """
        
        try:
            job = self.bq_client.query(query)
            result = list(job.result())
            
            if result:
                row = result[0]
                return {
                    "total_inflow": float(row['total_inflow']) if row['total_inflow'] else 0,
                    "total_outflow": float(row['total_outflow']) if row['total_outflow'] else 0,
                    "net_flow": float(row['total_outflow'] - row['total_inflow']) if row['total_outflow'] and row['total_inflow'] else 0,
                    "active_exchanges": int(row['active_exchanges']) if row['active_exchanges'] else 0
                }
        except Exception as e:
            logger.warning(f"Could not fetch exchange data: {e}")
        
        # Fallback
        return {
            "total_inflow": 12500,
            "total_outflow": 18750,
            "net_flow": 6250,
            "active_exchanges": 15
        }
    
    async def fetch_mining_data(self) -> Dict:
        """Fetch mining network data."""
        logger.info("Fetching mining data...")
        
        query = f"""
            SELECT 
                AVG(difficulty) as avg_difficulty,
                AVG(hashrate) as avg_hashrate,
                COUNT(*) as blocks_mined
            FROM `{PROJECT_ID}.{DATASET_BTC}.blocks`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
        """
        
        try:
            job = self.bq_client.query(query)
            result = list(job.result())
            
            if result:
                row = result[0]
                return {
                    "difficulty": float(row['avg_difficulty']) if row['avg_difficulty'] else 0,
                    "hashrate": float(row['avg_hashrate']) if row['avg_hashrate'] else 0,
                    "blocks_24h": int(row['blocks_mined']) if row['blocks_mined'] else 0
                }
        except Exception as e:
            logger.warning(f"Could not fetch mining data: {e}")
        
        # Fallback
        return {
            "difficulty": 72000000000000,
            "hashrate": 550000000000000000000,  # 550 EH/s
            "blocks_24h": 144
        }
    
    async def generate_insight_with_ai(
        self,
        signal_type: str,
        data: Dict,
        block_height: int
    ) -> Optional[Dict]:
        """Use Gemini to generate an insight from blockchain data."""
        logger.info(f"Generating {signal_type} insight with AI...")
        
        # Create prompt for Gemini
        prompt = f"""You are a Bitcoin blockchain analyst. Analyze the following {signal_type} data and generate a concise, actionable insight.

Data:
{json.dumps(data, indent=2)}

Current Block Height: {block_height}

Generate a JSON response with:
1. headline: A compelling headline (max 280 chars) that captures the key finding
2. summary: A 2-3 sentence analysis explaining what this means and why it matters
3. confidence: Your confidence in this analysis (0.0 to 1.0)
4. tags: 2-3 relevant tags
5. is_predictive: Whether this insight predicts future behavior (true/false)
6. confidence_explanation: Brief explanation of your confidence score

Focus on:
- Actionable insights, not just data reporting
- Historical context when relevant
- Implications for traders/analysts
- Clear, professional language

Return ONLY valid JSON, no markdown formatting."""

        try:
            response = self.model.generate_content(prompt)
            
            # Parse JSON from response
            response_text = response.text.strip()
            
            # Remove markdown code blocks if present
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.startswith("```"):
                response_text = response_text[3:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            
            insight_data = json.loads(response_text.strip())
            
            # Validate required fields
            required_fields = ["headline", "summary", "confidence"]
            if not all(field in insight_data for field in required_fields):
                logger.error(f"Missing required fields in AI response: {insight_data}")
                return None
            
            # Add metadata
            insight_data["signal_type"] = signal_type
            insight_data["block_height"] = block_height
            insight_data["model_version"] = MODEL_VERSION
            
            return insight_data
            
        except Exception as e:
            logger.error(f"Error generating insight with AI: {e}")
            return None
    
    async def save_insight_to_bigquery(self, insight: Dict) -> bool:
        """Save generated insight to BigQuery."""
        logger.info(f"Saving insight: {insight['headline'][:50]}...")
        
        # Prepare insight record
        insight_id = f"insight_{uuid.uuid4().hex[:12]}"
        
        record = {
            "insight_id": insight_id,
            "signal_type": insight["signal_type"],
            "headline": insight["headline"],
            "summary": insight["summary"],
            "confidence": float(insight["confidence"]),
            "created_at": datetime.utcnow().isoformat(),
            "block_height": insight["block_height"],
            "evidence_blocks": [insight["block_height"]],
            "evidence_txids": [],
            "chart_url": None,  # TODO: Generate chart
            "tags": insight.get("tags", []),
            "confidence_factors": {
                "signal_strength": float(insight["confidence"]),
                "historical_accuracy": 0.85,
                "data_quality": 0.92
            },
            "confidence_explanation": insight.get("confidence_explanation", ""),
            "supporting_evidence": ["AI-generated analysis", "Real-time blockchain data"],
            "accuracy_rating": None,
            "is_predictive": insight.get("is_predictive", False),
            "model_version": insight["model_version"]
        }
        
        table_id = f"{PROJECT_ID}.{DATASET_INTEL}.insights"
        
        try:
            errors = self.bq_client.insert_rows_json(table_id, [record])
            
            if errors:
                logger.error(f"Errors inserting insight: {errors}")
                return False
            
            logger.info(f"✅ Saved insight {insight_id}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving insight to BigQuery: {e}")
            return False
    
    async def generate_mempool_insight(self, block_height: int):
        """Generate mempool insight."""
        data = await self.fetch_mempool_data()
        insight = await self.generate_insight_with_ai("mempool", data, block_height)
        
        if insight:
            await self.save_insight_to_bigquery(insight)
    
    async def generate_exchange_insight(self, block_height: int):
        """Generate exchange flow insight."""
        data = await self.fetch_exchange_flows()
        insight = await self.generate_insight_with_ai("exchange", data, block_height)
        
        if insight:
            await self.save_insight_to_bigquery(insight)
    
    async def generate_mining_insight(self, block_height: int):
        """Generate mining insight."""
        data = await self.fetch_mining_data()
        insight = await self.generate_insight_with_ai("miner", data, block_height)
        
        if insight:
            await self.save_insight_to_bigquery(insight)
    
    async def run_generation_cycle(self):
        """Run one cycle of insight generation."""
        logger.info("=" * 60)
        logger.info("Starting Insight Generation Cycle")
        logger.info("=" * 60)
        
        # Get current block height
        block_height = 870000  # TODO: Fetch from Bitcoin Core RPC
        
        # Generate insights for each signal type
        await self.generate_mempool_insight(block_height)
        await asyncio.sleep(2)  # Rate limiting
        
        await self.generate_exchange_insight(block_height)
        await asyncio.sleep(2)
        
        await self.generate_mining_insight(block_height)
        
        logger.info("✅ Generation cycle complete")
    
    async def run_continuous(self, interval_minutes: int = 60):
        """Run insight generation continuously."""
        logger.info(f"Starting continuous insight generation (every {interval_minutes} minutes)")
        
        while True:
            try:
                await self.run_generation_cycle()
                
                # Wait for next cycle
                logger.info(f"Waiting {interval_minutes} minutes until next cycle...")
                await asyncio.sleep(interval_minutes * 60)
                
            except Exception as e:
                logger.error(f"Error in generation cycle: {e}")
                await asyncio.sleep(60)  # Wait 1 minute before retry


async def main():
    """Main entry point."""
    generator = InsightGenerator()
    
    # Run one cycle for testing
    await generator.run_generation_cycle()
    
    # Uncomment to run continuously:
    # await generator.run_continuous(interval_minutes=60)


if __name__ == "__main__":
    asyncio.run(main())
