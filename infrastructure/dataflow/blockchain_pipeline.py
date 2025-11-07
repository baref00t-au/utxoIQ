"""
Apache Beam / Dataflow pipeline for blockchain data processing
Handles data normalization, entity resolution, and BigQuery loading
"""

import apache_beam as beam
from apache_beam.options.pipeline_options import PipelineOptions, StandardOptions
from apache_beam.io.gcp.bigquery import WriteToBigQuery, BigQueryDisposition
from apache_beam.io.gcp.pubsub import ReadFromPubSub
import json
import logging
from typing import Dict, Any

logger = logging.getLogger(__name__)


class ParsePubSubMessage(beam.DoFn):
    """Parse Pub/Sub message JSON"""
    
    def process(self, element):
        try:
            data = json.loads(element.decode('utf-8'))
            yield data
        except Exception as e:
            logger.error(f"Failed to parse message: {str(e)}")


class EnrichWithEntityData(beam.DoFn):
    """Enrich transaction data with entity information"""
    
    def __init__(self, entity_mapping_path: str = None):
        self.entity_mapping = {}
        self.entity_mapping_path = entity_mapping_path
    
    def setup(self):
        """Load entity mapping data"""
        # In production, load from Cloud Storage or BigQuery
        # For now, use a simple in-memory mapping
        self.entity_mapping = {
            # Example entity mappings (address -> entity info)
            # This would be loaded from a maintained database
        }
    
    def process(self, transaction: Dict):
        """Add entity tags to transaction"""
        enriched = transaction.copy()
        enriched['entities'] = []
        
        # Check inputs for known entities
        for vin in transaction.get('inputs', []):
            address = vin.get('address')
            if address and address in self.entity_mapping:
                entity_info = self.entity_mapping[address]
                enriched['entities'].append({
                    'address': address,
                    'type': entity_info.get('type'),
                    'name': entity_info.get('name'),
                    'direction': 'input'
                })
        
        # Check outputs for known entities
        for vout in transaction.get('outputs', []):
            address = vout.get('address')
            if address and address in self.entity_mapping:
                entity_info = self.entity_mapping[address]
                enriched['entities'].append({
                    'address': address,
                    'type': entity_info.get('type'),
                    'name': entity_info.get('name'),
                    'direction': 'output'
                })
        
        yield enriched


class ValidateBlockData(beam.DoFn):
    """Validate block data before loading to BigQuery"""
    
    def process(self, block: Dict):
        """Validate required fields"""
        required_fields = ['block_hash', 'height', 'timestamp', 'size', 'tx_count', 'fees_total']
        
        if all(field in block for field in required_fields):
            # Ensure correct types
            try:
                validated = {
                    'block_hash': str(block['block_hash']),
                    'height': int(block['height']),
                    'timestamp': int(block['timestamp']),
                    'size': int(block['size']),
                    'tx_count': int(block['tx_count']),
                    'fees_total': int(block['fees_total'])
                }
                yield validated
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid block data types: {str(e)}")
        else:
            logger.error(f"Missing required fields in block data")


class ValidateTransactionData(beam.DoFn):
    """Validate transaction data before loading to BigQuery"""
    
    def process(self, transaction: Dict):
        """Validate required fields"""
        required_fields = ['tx_hash', 'block_height', 'input_count', 'output_count', 'fee', 'size']
        
        if all(field in transaction for field in required_fields):
            try:
                validated = {
                    'tx_hash': str(transaction['tx_hash']),
                    'block_height': int(transaction['block_height']),
                    'input_count': int(transaction['input_count']),
                    'output_count': int(transaction['output_count']),
                    'fee': int(transaction['fee']),
                    'size': int(transaction['size'])
                }
                yield validated
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid transaction data types: {str(e)}")
        else:
            logger.error(f"Missing required fields in transaction data")


def run_pipeline(project_id: str, region: str = 'us-central1'):
    """Run the Dataflow pipeline"""
    
    # Pipeline options
    options = PipelineOptions(
        project=project_id,
        region=region,
        runner='DataflowRunner',
        streaming=True,
        save_main_session=True
    )
    
    # BigQuery table schemas
    block_schema = {
        'fields': [
            {'name': 'block_hash', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'height', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'timestamp', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'size', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'tx_count', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'fees_total', 'type': 'INTEGER', 'mode': 'REQUIRED'}
        ]
    }
    
    transaction_schema = {
        'fields': [
            {'name': 'tx_hash', 'type': 'STRING', 'mode': 'REQUIRED'},
            {'name': 'block_height', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'input_count', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'output_count', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'fee', 'type': 'INTEGER', 'mode': 'REQUIRED'},
            {'name': 'size', 'type': 'INTEGER', 'mode': 'REQUIRED'}
        ]
    }
    
    with beam.Pipeline(options=options) as pipeline:
        # Process blocks
        blocks = (
            pipeline
            | 'Read Blocks from Pub/Sub' >> ReadFromPubSub(
                subscription=f'projects/{project_id}/subscriptions/btc-blocks-sub'
            )
            | 'Parse Block Messages' >> beam.ParDo(ParsePubSubMessage())
            | 'Validate Blocks' >> beam.ParDo(ValidateBlockData())
            | 'Write Blocks to BigQuery' >> WriteToBigQuery(
                table=f'{project_id}:btc.blocks',
                schema=block_schema,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_NEVER
            )
        )
        
        # Process transactions
        transactions = (
            pipeline
            | 'Read Transactions from Pub/Sub' >> ReadFromPubSub(
                subscription=f'projects/{project_id}/subscriptions/btc-transactions-sub'
            )
            | 'Parse Transaction Messages' >> beam.ParDo(ParsePubSubMessage())
            | 'Enrich with Entities' >> beam.ParDo(EnrichWithEntityData())
            | 'Validate Transactions' >> beam.ParDo(ValidateTransactionData())
            | 'Write Transactions to BigQuery' >> WriteToBigQuery(
                table=f'{project_id}:btc.transactions',
                schema=transaction_schema,
                write_disposition=BigQueryDisposition.WRITE_APPEND,
                create_disposition=BigQueryDisposition.CREATE_NEVER
            )
        )


if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser()
    parser.add_argument('--project', required=True, help='GCP project ID')
    parser.add_argument('--region', default='us-central1', help='GCP region')
    
    args = parser.parse_args()
    
    logging.basicConfig(level=logging.INFO)
    run_pipeline(args.project, args.region)
