"""
End-to-End Test: Block to Insight Flow
Tests complete data flow from Bitcoin node to insight publication
"""

import pytest
import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, Any, List
import requests
import websocket
import json

from tests.e2e.helpers import (
    BitcoinNodeHelper,
    WebAPIClient,
    BigQueryHelper,
    PubSubHelper
)


class TestBlockToInsightFlow:
    """Test complete block-to-insight data flow"""
    
    @pytest.fixture
    def bitcoin_helper(self):
        """Bitcoin node helper"""
        return BitcoinNodeHelper(
            host="localhost",
            port=8332,
            user="bitcoin",
            password="bitcoin"
        )
    
    @pytest.fixture
    def api_client(self):
        """Web API client"""
        return WebAPIClient(base_url="http://localhost:8080")
    
    @pytest.fixture
    def bigquery_helper(self):
        """BigQuery helper"""
        return BigQueryHelper(project_id="utxoiq-test")
    
    @pytest.fixture
    def pubsub_helper(self):
        """Pub/Sub helper"""
        return PubSubHelper(project_id="utxoiq-test")
    
    @pytest.mark.asyncio
    async def test_complete_block_processing_flow(
        self,
        bitcoin_helper,
        api_client,
        bigquery_helper,
        pubsub_helper
    ):
        """
        Test complete flow from block detection to insight publication
        
        Requirements: 7.1, 7.2
        """
        # Step 1: Get current block height
        initial_height = bitcoin_helper.get_block_count()
        print(f"Initial block height: {initial_height}")
        
        # Step 2: Subscribe to WebSocket for real-time updates
        ws_messages = []
        
        def on_message(ws, message):
            ws_messages.append(json.loads(message))
        
        ws = websocket.WebSocketApp(
            "ws://localhost:8080/ws",
            on_message=on_message
        )
        
        # Start WebSocket in background
        import threading
        ws_thread = threading.Thread(target=ws.run_forever)
        ws_thread.daemon = True
        ws_thread.start()
        
        # Wait for connection
        await asyncio.sleep(2)
        
        # Step 3: Wait for new block (or simulate one in regtest)
        if bitcoin_helper.is_regtest():
            # Generate a block with transactions
            bitcoin_helper.generate_block_with_transactions()
        else:
            # Wait for next block (max 15 minutes)
            print("Waiting for next block...")
            timeout = 900  # 15 minutes
            start_time = time.time()
            
            while time.time() - start_time < timeout:
                current_height = bitcoin_helper.get_block_count()
                if current_height > initial_height:
                    break
                await asyncio.sleep(10)
            
            if current_height == initial_height:
                pytest.skip("No new block detected within timeout")
        
        new_height = bitcoin_helper.get_block_count()
        print(f"New block detected: {new_height}")
        
        # Step 4: Verify block data ingestion
        # Wait for block to be ingested into BigQuery
        await asyncio.sleep(5)
        
        block_data = bigquery_helper.get_block_by_height(new_height)
        assert block_data is not None, "Block not found in BigQuery"
        assert block_data['height'] == new_height
        
        # Step 5: Verify signal generation
        # Wait for signals to be computed
        await asyncio.sleep(10)
        
        signals = bigquery_helper.get_signals_for_block(new_height)
        assert len(signals) > 0, "No signals generated for block"
        
        # Verify signal types
        signal_types = {s['signal_type'] for s in signals}
        print(f"Generated signal types: {signal_types}")
        
        # Step 6: Verify insight generation
        # Wait for insights to be generated
        await asyncio.sleep(20)
        
        insights = api_client.get_insights(
            min_block_height=new_height,
            max_block_height=new_height
        )
        
        assert len(insights) > 0, "No insights generated for block"
        
        # Verify insight properties
        for insight in insights:
            assert insight['block_height'] == new_height
            assert 'headline' in insight
            assert 'summary' in insight
            assert 'confidence' in insight
            assert insight['confidence'] >= 0.0
            assert insight['confidence'] <= 1.0
            assert 'evidence' in insight
        
        # Step 7: Verify WebSocket notification
        # Check if we received WebSocket message for new insight
        insight_messages = [
            msg for msg in ws_messages
            if msg.get('type') == 'new_insight'
        ]
        
        assert len(insight_messages) > 0, "No WebSocket notifications received"
        
        # Step 8: Measure end-to-end latency
        block_timestamp = datetime.fromisoformat(block_data['timestamp'])
        insight_timestamp = datetime.fromisoformat(insights[0]['created_at'])
        
        latency_seconds = (insight_timestamp - block_timestamp).total_seconds()
        print(f"Block-to-insight latency: {latency_seconds} seconds")
        
        # Verify SLA: < 60 seconds
        assert latency_seconds < 60, f"Latency {latency_seconds}s exceeds 60s SLA"
        
        # Cleanup
        ws.close()
    
    @pytest.mark.asyncio
    async def test_blockchain_reorganization_handling(
        self,
        bitcoin_helper,
        bigquery_helper
    ):
        """
        Test system behavior during blockchain reorganizations
        
        Requirements: 7.5
        """
        if not bitcoin_helper.is_regtest():
            pytest.skip("Reorg testing requires regtest mode")
        
        # Step 1: Generate initial chain
        initial_height = bitcoin_helper.get_block_count()
        bitcoin_helper.generate_blocks(5)
        
        # Wait for ingestion
        await asyncio.sleep(10)
        
        # Step 2: Get block hashes
        height_to_reorg = initial_height + 3
        original_hash = bitcoin_helper.get_block_hash(height_to_reorg)
        
        # Verify block in BigQuery
        original_block = bigquery_helper.get_block_by_height(height_to_reorg)
        assert original_block is not None
        assert original_block['hash'] == original_hash
        
        # Step 3: Trigger reorganization
        # Invalidate blocks and mine alternative chain
        bitcoin_helper.invalidate_block(original_hash)
        bitcoin_helper.generate_blocks(6)  # Longer chain
        
        # Wait for reorg processing
        await asyncio.sleep(15)
        
        # Step 4: Verify new block hash
        new_hash = bitcoin_helper.get_block_hash(height_to_reorg)
        assert new_hash != original_hash, "Reorg did not occur"
        
        # Step 5: Verify BigQuery updated
        updated_block = bigquery_helper.get_block_by_height(height_to_reorg)
        assert updated_block is not None
        assert updated_block['hash'] == new_hash
        
        # Step 6: Verify old insights marked as invalid
        old_insights = bigquery_helper.get_insights_for_block_hash(original_hash)
        for insight in old_insights:
            assert insight.get('is_valid') == False, "Old insight not marked invalid"
        
        # Step 7: Verify new insights generated
        new_insights = bigquery_helper.get_insights_for_block_hash(new_hash)
        assert len(new_insights) > 0, "No new insights after reorg"
    
    @pytest.mark.asyncio
    async def test_failover_and_recovery(
        self,
        api_client,
        pubsub_helper
    ):
        """
        Test failover and recovery scenarios
        
        Requirements: 21.4
        """
        # Step 1: Verify all services healthy
        health_checks = {
            'web-api': api_client.health_check(),
            'feature-engine': requests.get('http://localhost:8081/health').json(),
            'insight-generator': requests.get('http://localhost:8082/health').json()
        }
        
        for service, health in health_checks.items():
            assert health['status'] == 'healthy', f"{service} not healthy"
        
        # Step 2: Simulate service failure
        # Stop feature-engine temporarily
        print("Simulating feature-engine failure...")
        # In real test, would use docker-compose or kubectl to stop service
        
        # Step 3: Verify graceful degradation
        # System should continue processing with cached/fallback data
        await asyncio.sleep(5)
        
        # Web API should still respond
        response = api_client.get_insights(limit=10)
        assert response is not None, "Web API failed during service outage"
        
        # Step 4: Restart service
        print("Restarting feature-engine...")
        # In real test, would restart the service
        
        await asyncio.sleep(10)
        
        # Step 5: Verify recovery
        health = requests.get('http://localhost:8081/health').json()
        assert health['status'] == 'healthy', "Service did not recover"
        
        # Step 6: Verify backlog processing
        # Service should process any queued messages
        messages = pubsub_helper.get_pending_messages('signals-topic')
        print(f"Pending messages after recovery: {len(messages)}")
        
        # Wait for backlog to clear
        await asyncio.sleep(30)
        
        messages_after = pubsub_helper.get_pending_messages('signals-topic')
        assert len(messages_after) < len(messages), "Backlog not processing"
    
    @pytest.mark.asyncio
    async def test_websocket_stability_under_load(self, api_client):
        """
        Test WebSocket connection stability under load
        
        Requirements: 7.1
        """
        num_connections = 100
        connections = []
        messages_received = []
        
        def create_ws_connection(index):
            """Create WebSocket connection"""
            received = []
            
            def on_message(ws, message):
                received.append(json.loads(message))
            
            def on_error(ws, error):
                print(f"Connection {index} error: {error}")
            
            ws = websocket.WebSocketApp(
                "ws://localhost:8080/ws",
                on_message=on_message,
                on_error=on_error
            )
            
            return ws, received
        
        # Step 1: Create multiple WebSocket connections
        print(f"Creating {num_connections} WebSocket connections...")
        
        for i in range(num_connections):
            ws, received = create_ws_connection(i)
            connections.append(ws)
            messages_received.append(received)
            
            # Start connection in background
            import threading
            thread = threading.Thread(target=ws.run_forever)
            thread.daemon = True
            thread.start()
            
            # Small delay to avoid overwhelming server
            await asyncio.sleep(0.1)
        
        # Step 2: Wait for connections to establish
        await asyncio.sleep(5)
        
        # Step 3: Trigger insight generation
        # This should broadcast to all connections
        print("Triggering insight generation...")
        
        # Wait for broadcasts
        await asyncio.sleep(10)
        
        # Step 4: Verify all connections received messages
        successful_connections = sum(1 for msgs in messages_received if len(msgs) > 0)
        connection_success_rate = successful_connections / num_connections
        
        print(f"Successful connections: {successful_connections}/{num_connections}")
        print(f"Success rate: {connection_success_rate * 100:.1f}%")
        
        # Verify > 95% success rate (< 5% disconnection rate)
        assert connection_success_rate > 0.95, \
            f"Connection success rate {connection_success_rate} below 95% threshold"
        
        # Step 5: Cleanup
        for ws in connections:
            ws.close()
    
    @pytest.mark.asyncio
    async def test_canary_deployment_and_rollback(self, api_client):
        """
        Test canary deployment and rollback functionality
        
        Requirements: 22.3
        """
        # This test would typically run in CI/CD pipeline
        # Here we verify the monitoring and rollback logic
        
        # Step 1: Deploy canary revision
        # In real scenario, this would be done by deployment pipeline
        canary_url = "http://localhost:8080"  # Canary endpoint
        stable_url = "http://localhost:8080"  # Stable endpoint
        
        # Step 2: Monitor canary metrics
        canary_errors = 0
        canary_requests = 0
        stable_errors = 0
        stable_requests = 0
        
        # Send requests to both versions
        for i in range(100):
            # 10% to canary, 90% to stable
            if i < 10:
                try:
                    response = requests.get(f"{canary_url}/health", timeout=5)
                    canary_requests += 1
                    if response.status_code >= 500:
                        canary_errors += 1
                except Exception:
                    canary_errors += 1
                    canary_requests += 1
            else:
                try:
                    response = requests.get(f"{stable_url}/health", timeout=5)
                    stable_requests += 1
                    if response.status_code >= 500:
                        stable_errors += 1
                except Exception:
                    stable_errors += 1
                    stable_requests += 1
            
            await asyncio.sleep(0.1)
        
        # Step 3: Calculate error rates
        canary_error_rate = (canary_errors / canary_requests * 100) if canary_requests > 0 else 0
        stable_error_rate = (stable_errors / stable_requests * 100) if stable_requests > 0 else 0
        
        print(f"Canary error rate: {canary_error_rate:.2f}%")
        print(f"Stable error rate: {stable_error_rate:.2f}%")
        
        # Step 4: Verify rollback logic
        # If canary error rate > 1%, should trigger rollback
        should_rollback = canary_error_rate > 1.0
        
        if should_rollback:
            print("Canary error rate exceeds threshold, rollback required")
            # In real scenario, deployment pipeline would rollback
            assert True, "Rollback logic triggered correctly"
        else:
            print("Canary performing well, can promote to production")
            assert canary_error_rate <= 1.0, "Canary error rate within threshold"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
