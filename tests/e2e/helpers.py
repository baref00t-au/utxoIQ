"""
Helper classes for end-to-end tests
"""

import requests
import json
from typing import Dict, Any, List, Optional
from google.cloud import bigquery
from google.cloud import pubsub_v1
from datetime import datetime


class BitcoinNodeHelper:
    """Helper for interacting with Bitcoin node"""
    
    def __init__(self, host: str, port: int, user: str, password: str):
        self.host = host
        self.port = port
        self.user = user
        self.password = password
        self.url = f"http://{host}:{port}"
    
    def _rpc_call(self, method: str, params: List = None) -> Any:
        """Make RPC call to Bitcoin node"""
        payload = {
            "jsonrpc": "1.0",
            "id": "test",
            "method": method,
            "params": params or []
        }
        
        response = requests.post(
            self.url,
            auth=(self.user, self.password),
            json=payload,
            headers={"content-type": "application/json"}
        )
        
        response.raise_for_status()
        result = response.json()
        
        if result.get('error'):
            raise Exception(f"RPC error: {result['error']}")
        
        return result['result']
    
    def get_block_count(self) -> int:
        """Get current block height"""
        return self._rpc_call("getblockcount")
    
    def get_block_hash(self, height: int) -> str:
        """Get block hash at height"""
        return self._rpc_call("getblockhash", [height])
    
    def get_block(self, block_hash: str) -> Dict[str, Any]:
        """Get block data"""
        return self._rpc_call("getblock", [block_hash, 2])
    
    def generate_blocks(self, count: int) -> List[str]:
        """Generate blocks (regtest only)"""
        return self._rpc_call("generate", [count])
    
    def generate_block_with_transactions(self) -> str:
        """Generate a block with transactions (regtest only)"""
        # Create some transactions first
        address = self._rpc_call("getnewaddress")
        self._rpc_call("sendtoaddress", [address, 1.0])
        
        # Mine block
        blocks = self.generate_blocks(1)
        return blocks[0]
    
    def invalidate_block(self, block_hash: str):
        """Invalidate a block (for reorg testing)"""
        self._rpc_call("invalidateblock", [block_hash])
    
    def is_regtest(self) -> bool:
        """Check if node is in regtest mode"""
        blockchain_info = self._rpc_call("getblockchaininfo")
        return blockchain_info.get('chain') == 'regtest'


class WebAPIClient:
    """Helper for interacting with Web API"""
    
    def __init__(self, base_url: str, api_key: Optional[str] = None):
        self.base_url = base_url.rstrip('/')
        self.api_key = api_key
        self.session = requests.Session()
        
        if api_key:
            self.session.headers['X-API-Key'] = api_key
    
    def health_check(self) -> Dict[str, Any]:
        """Check API health"""
        response = self.session.get(f"{self.base_url}/health")
        response.raise_for_status()
        return response.json()
    
    def get_insights(
        self,
        limit: int = 20,
        offset: int = 0,
        category: Optional[str] = None,
        min_confidence: Optional[float] = None,
        min_block_height: Optional[int] = None,
        max_block_height: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """Get insights"""
        params = {
            'limit': limit,
            'offset': offset
        }
        
        if category:
            params['category'] = category
        if min_confidence is not None:
            params['min_confidence'] = min_confidence
        if min_block_height is not None:
            params['min_block_height'] = min_block_height
        if max_block_height is not None:
            params['max_block_height'] = max_block_height
        
        response = self.session.get(
            f"{self.base_url}/api/v1/insights",
            params=params
        )
        response.raise_for_status()
        return response.json()['insights']
    
    def get_insight(self, insight_id: str) -> Dict[str, Any]:
        """Get single insight"""
        response = self.session.get(f"{self.base_url}/api/v1/insights/{insight_id}")
        response.raise_for_status()
        return response.json()
    
    def create_alert(self, alert_data: Dict[str, Any]) -> Dict[str, Any]:
        """Create alert"""
        response = self.session.post(
            f"{self.base_url}/api/v1/alerts",
            json=alert_data
        )
        response.raise_for_status()
        return response.json()
    
    def get_daily_brief(self, date: Optional[str] = None) -> Dict[str, Any]:
        """Get daily brief"""
        params = {}
        if date:
            params['date'] = date
        
        response = self.session.get(
            f"{self.base_url}/api/v1/daily-brief",
            params=params
        )
        response.raise_for_status()
        return response.json()


class BigQueryHelper:
    """Helper for interacting with BigQuery"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
    
    def query(self, sql: str) -> List[Dict[str, Any]]:
        """Execute query and return results"""
        query_job = self.client.query(sql)
        results = query_job.result()
        
        return [dict(row) for row in results]
    
    def get_block_by_height(self, height: int) -> Optional[Dict[str, Any]]:
        """Get block by height"""
        sql = f"""
        SELECT *
        FROM `{self.project_id}.btc.blocks`
        WHERE height = {height}
        LIMIT 1
        """
        
        results = self.query(sql)
        return results[0] if results else None
    
    def get_block_by_hash(self, block_hash: str) -> Optional[Dict[str, Any]]:
        """Get block by hash"""
        sql = f"""
        SELECT *
        FROM `{self.project_id}.btc.blocks`
        WHERE hash = '{block_hash}'
        LIMIT 1
        """
        
        results = self.query(sql)
        return results[0] if results else None
    
    def get_signals_for_block(self, block_height: int) -> List[Dict[str, Any]]:
        """Get signals for block"""
        sql = f"""
        SELECT *
        FROM `{self.project_id}.intel.signals`
        WHERE block_height = {block_height}
        ORDER BY created_at DESC
        """
        
        return self.query(sql)
    
    def get_insights_for_block_hash(self, block_hash: str) -> List[Dict[str, Any]]:
        """Get insights for block hash"""
        sql = f"""
        SELECT i.*
        FROM `{self.project_id}.intel.insights` i
        JOIN `{self.project_id}.btc.blocks` b
          ON i.block_height = b.height
        WHERE b.hash = '{block_hash}'
        ORDER BY i.created_at DESC
        """
        
        return self.query(sql)
    
    def get_latest_insights(self, limit: int = 10) -> List[Dict[str, Any]]:
        """Get latest insights"""
        sql = f"""
        SELECT *
        FROM `{self.project_id}.intel.insights`
        ORDER BY created_at DESC
        LIMIT {limit}
        """
        
        return self.query(sql)
    
    def get_metrics_for_period(
        self,
        start_time: datetime,
        end_time: datetime
    ) -> Dict[str, Any]:
        """Get metrics for time period"""
        sql = f"""
        SELECT
          COUNT(*) as total_insights,
          AVG(confidence) as avg_confidence,
          COUNT(DISTINCT block_height) as blocks_processed,
          AVG(TIMESTAMP_DIFF(created_at, block_timestamp, SECOND)) as avg_latency_seconds
        FROM `{self.project_id}.intel.insights`
        WHERE created_at BETWEEN '{start_time.isoformat()}' AND '{end_time.isoformat()}'
        """
        
        results = self.query(sql)
        return results[0] if results else {}


class PubSubHelper:
    """Helper for interacting with Pub/Sub"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.publisher = pubsub_v1.PublisherClient()
        self.subscriber = pubsub_v1.SubscriberClient()
    
    def publish_message(self, topic_name: str, data: Dict[str, Any]) -> str:
        """Publish message to topic"""
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        
        message_data = json.dumps(data).encode('utf-8')
        future = self.publisher.publish(topic_path, message_data)
        
        return future.result()
    
    def get_pending_messages(self, topic_name: str) -> List[Dict[str, Any]]:
        """Get pending messages from subscription"""
        subscription_name = f"{topic_name}-test-sub"
        subscription_path = self.subscriber.subscription_path(
            self.project_id,
            subscription_name
        )
        
        # Pull messages
        response = self.subscriber.pull(
            request={
                "subscription": subscription_path,
                "max_messages": 100
            }
        )
        
        messages = []
        ack_ids = []
        
        for received_message in response.received_messages:
            data = json.loads(received_message.message.data.decode('utf-8'))
            messages.append(data)
            ack_ids.append(received_message.ack_id)
        
        # Acknowledge messages
        if ack_ids:
            self.subscriber.acknowledge(
                request={
                    "subscription": subscription_path,
                    "ack_ids": ack_ids
                }
            )
        
        return messages
    
    def create_test_subscription(self, topic_name: str):
        """Create test subscription"""
        topic_path = self.publisher.topic_path(self.project_id, topic_name)
        subscription_name = f"{topic_name}-test-sub"
        subscription_path = self.subscriber.subscription_path(
            self.project_id,
            subscription_name
        )
        
        try:
            self.subscriber.create_subscription(
                request={
                    "name": subscription_path,
                    "topic": topic_path
                }
            )
        except Exception:
            # Subscription already exists
            pass
    
    def delete_test_subscription(self, topic_name: str):
        """Delete test subscription"""
        subscription_name = f"{topic_name}-test-sub"
        subscription_path = self.subscriber.subscription_path(
            self.project_id,
            subscription_name
        )
        
        try:
            self.subscriber.delete_subscription(
                request={"subscription": subscription_path}
            )
        except Exception:
            pass
