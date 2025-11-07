#!/usr/bin/env python3
"""
BigQuery Optimization Monitor
Monitors query performance, costs, and provides optimization recommendations
"""

import os
import sys
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from google.cloud import bigquery
from google.cloud import monitoring_v3
import argparse


class BigQueryOptimizationMonitor:
    """Monitor and optimize BigQuery usage for utxoIQ platform"""
    
    def __init__(self, project_id: str):
        self.project_id = project_id
        self.client = bigquery.Client(project=project_id)
        self.monitoring_client = monitoring_v3.MetricServiceClient()
        
    def check_partition_usage(self) -> Dict[str, any]:
        """Check if queries are using partition pruning"""
        query = f"""
        SELECT
          user_email,
          query,
          total_bytes_processed / POW(10, 9) as gb_processed,
          total_bytes_billed / POW(10, 9) as gb_billed,
          CASE
            WHEN query LIKE '%WHERE%processed_at%' OR 
                 query LIKE '%WHERE%created_at%' OR 
                 query LIKE '%WHERE%timestamp%' THEN 'Using partition filter'
            ELSE 'Missing partition filter'
          END as partition_status
        FROM `{self.project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE 
          creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
          AND job_type = 'QUERY'
          AND state = 'DONE'
          AND total_bytes_processed > POW(10, 10)  -- > 10 GB
        ORDER BY total_bytes_processed DESC
        LIMIT 20
        """
        
        results = self.client.query(query).result()
        
        partition_stats = {
            'total_queries': 0,
            'using_partition': 0,
            'missing_partition': 0,
            'queries': []
        }
        
        for row in results:
            partition_stats['total_queries'] += 1
            if row.partition_status == 'Using partition filter':
                partition_stats['using_partition'] += 1
            else:
                partition_stats['missing_partition'] += 1
            
            partition_stats['queries'].append({
                'user': row.user_email,
                'gb_processed': round(row.gb_processed, 2),
                'gb_billed': round(row.gb_billed, 2),
                'status': row.partition_status,
                'query': row.query[:200]  # First 200 chars
            })
        
        return partition_stats
    
    def get_daily_costs(self, days: int = 7) -> List[Dict]:
        """Get daily BigQuery costs for the last N days"""
        query = f"""
        SELECT
          DATE(creation_time) as query_date,
          COUNT(*) as query_count,
          SUM(total_bytes_processed) / POW(10, 12) as total_tb_processed,
          SUM(total_bytes_billed) / POW(10, 12) as total_tb_billed,
          SUM(total_bytes_billed) / POW(10, 12) * 5 as estimated_cost_usd
        FROM `{self.project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE 
          creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
          AND job_type = 'QUERY'
          AND state = 'DONE'
        GROUP BY query_date
        ORDER BY query_date DESC
        """
        
        results = self.client.query(query).result()
        
        daily_costs = []
        for row in results:
            daily_costs.append({
                'date': row.query_date.strftime('%Y-%m-%d'),
                'query_count': row.query_count,
                'tb_processed': round(row.total_tb_processed, 3),
                'tb_billed': round(row.total_tb_billed, 3),
                'cost_usd': round(row.estimated_cost_usd, 2)
            })
        
        return daily_costs
    
    def get_expensive_queries(self, limit: int = 10) -> List[Dict]:
        """Get the most expensive queries in the last 24 hours"""
        query = f"""
        SELECT
          user_email,
          query,
          creation_time,
          total_bytes_processed / POW(10, 9) as gb_processed,
          total_bytes_billed / POW(10, 9) as gb_billed,
          total_bytes_billed / POW(10, 12) * 5 as estimated_cost_usd,
          total_slot_ms / 1000 as total_seconds
        FROM `{self.project_id}.region-us.INFORMATION_SCHEMA.JOBS_BY_PROJECT`
        WHERE 
          creation_time >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
          AND job_type = 'QUERY'
          AND state = 'DONE'
        ORDER BY total_bytes_billed DESC
        LIMIT {limit}
        """
        
        results = self.client.query(query).result()
        
        expensive_queries = []
        for row in results:
            expensive_queries.append({
                'user': row.user_email,
                'timestamp': row.creation_time.strftime('%Y-%m-%d %H:%M:%S'),
                'gb_processed': round(row.gb_processed, 2),
                'gb_billed': round(row.gb_billed, 2),
                'cost_usd': round(row.estimated_cost_usd, 4),
                'duration_sec': round(row.total_seconds, 2),
                'query': row.query[:200]
            })
        
        return expensive_queries
    
    def get_table_sizes(self) -> List[Dict]:
        """Get size of all tables in intel and btc datasets"""
        query = f"""
        SELECT
          table_schema,
          table_name,
          ROUND(size_bytes / POW(10, 9), 2) as size_gb,
          row_count,
          CASE
            WHEN table_name LIKE '%signals%' THEN 'Signals'
            WHEN table_name LIKE '%insights%' THEN 'Insights'
            WHEN table_name LIKE '%feedback%' THEN 'Feedback'
            WHEN table_name LIKE '%blocks%' THEN 'Blocks'
            ELSE 'Other'
          END as table_category
        FROM `{self.project_id}.intel.__TABLES__`
        UNION ALL
        SELECT
          table_schema,
          table_name,
          ROUND(size_bytes / POW(10, 9), 2) as size_gb,
          row_count,
          'Blocks' as table_category
        FROM `{self.project_id}.btc.__TABLES__`
        ORDER BY size_gb DESC
        """
        
        results = self.client.query(query).result()
        
        table_sizes = []
        for row in results:
            table_sizes.append({
                'dataset': row.table_schema,
                'table': row.table_name,
                'size_gb': row.size_gb,
                'row_count': row.row_count,
                'category': row.table_category
            })
        
        return table_sizes
    
    def get_archival_candidates(self, age_days: int = 730) -> Dict:
        """Identify data that should be archived"""
        cutoff_date = (datetime.now() - timedelta(days=age_days)).strftime('%Y-%m-%d')
        
        queries = {
            'signals': f"""
                SELECT 
                    COUNT(*) as row_count,
                    MIN(DATE(processed_at)) as oldest_date,
                    MAX(DATE(processed_at)) as newest_date,
                    SUM(1) as rows_to_archive
                FROM `{self.project_id}.intel.signals`
                WHERE DATE(processed_at) < '{cutoff_date}'
            """,
            'insights': f"""
                SELECT 
                    COUNT(*) as row_count,
                    MIN(DATE(created_at)) as oldest_date,
                    MAX(DATE(created_at)) as newest_date,
                    SUM(1) as rows_to_archive
                FROM `{self.project_id}.intel.insights`
                WHERE DATE(created_at) < '{cutoff_date}'
            """,
            'feedback': f"""
                SELECT 
                    COUNT(*) as row_count,
                    MIN(DATE(timestamp)) as oldest_date,
                    MAX(DATE(timestamp)) as newest_date,
                    SUM(1) as rows_to_archive
                FROM `{self.project_id}.intel.user_feedback`
                WHERE DATE(timestamp) < '{cutoff_date}'
            """
        }
        
        archival_candidates = {}
        for table_name, query in queries.items():
            try:
                result = list(self.client.query(query).result())[0]
                archival_candidates[table_name] = {
                    'rows_to_archive': result.rows_to_archive or 0,
                    'oldest_date': str(result.oldest_date) if result.oldest_date else 'N/A',
                    'newest_date': str(result.newest_date) if result.newest_date else 'N/A'
                }
            except Exception as e:
                archival_candidates[table_name] = {
                    'error': str(e)
                }
        
        return archival_candidates
    
    def generate_report(self) -> str:
        """Generate comprehensive optimization report"""
        report = []
        report.append("=" * 80)
        report.append("BigQuery Optimization Report")
        report.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Project: {self.project_id}")
        report.append("=" * 80)
        report.append("")
        
        # Daily costs
        report.append("📊 DAILY COSTS (Last 7 Days)")
        report.append("-" * 80)
        daily_costs = self.get_daily_costs(7)
        total_cost = sum(d['cost_usd'] for d in daily_costs)
        report.append(f"{'Date':<12} {'Queries':<10} {'TB Processed':<15} {'TB Billed':<15} {'Cost (USD)':<12}")
        report.append("-" * 80)
        for cost in daily_costs:
            report.append(
                f"{cost['date']:<12} {cost['query_count']:<10} "
                f"{cost['tb_processed']:<15.3f} {cost['tb_billed']:<15.3f} "
                f"${cost['cost_usd']:<11.2f}"
            )
        report.append("-" * 80)
        report.append(f"Total Cost (7 days): ${total_cost:.2f}")
        report.append(f"Projected Monthly Cost: ${total_cost * 30 / 7:.2f}")
        report.append("")
        
        # Partition usage
        report.append("🔍 PARTITION FILTER USAGE (Last 24 Hours)")
        report.append("-" * 80)
        partition_stats = self.check_partition_usage()
        report.append(f"Total Large Queries (>10GB): {partition_stats['total_queries']}")
        report.append(f"Using Partition Filters: {partition_stats['using_partition']} "
                     f"({partition_stats['using_partition']/max(partition_stats['total_queries'], 1)*100:.1f}%)")
        report.append(f"Missing Partition Filters: {partition_stats['missing_partition']} "
                     f"({partition_stats['missing_partition']/max(partition_stats['total_queries'], 1)*100:.1f}%)")
        
        if partition_stats['missing_partition'] > 0:
            report.append("")
            report.append("⚠️  Queries Missing Partition Filters:")
            for q in partition_stats['queries']:
                if q['status'] == 'Missing partition filter':
                    report.append(f"  - User: {q['user']}, GB Processed: {q['gb_processed']}")
                    report.append(f"    Query: {q['query'][:100]}...")
        report.append("")
        
        # Expensive queries
        report.append("💰 MOST EXPENSIVE QUERIES (Last 24 Hours)")
        report.append("-" * 80)
        expensive = self.get_expensive_queries(5)
        for i, q in enumerate(expensive, 1):
            report.append(f"{i}. Cost: ${q['cost_usd']:.4f} | GB Billed: {q['gb_billed']} | "
                         f"Duration: {q['duration_sec']}s")
            report.append(f"   User: {q['user']} | Time: {q['timestamp']}")
            report.append(f"   Query: {q['query'][:150]}...")
            report.append("")
        
        # Table sizes
        report.append("📦 TABLE SIZES")
        report.append("-" * 80)
        table_sizes = self.get_table_sizes()
        total_size = sum(t['size_gb'] for t in table_sizes)
        report.append(f"{'Dataset':<15} {'Table':<30} {'Size (GB)':<12} {'Rows':<15}")
        report.append("-" * 80)
        for table in table_sizes[:10]:  # Top 10 tables
            report.append(
                f"{table['dataset']:<15} {table['table']:<30} "
                f"{table['size_gb']:<12.2f} {table['row_count']:<15,}"
            )
        report.append("-" * 80)
        report.append(f"Total Storage: {total_size:.2f} GB")
        report.append("")
        
        # Archival candidates
        report.append("🗄️  ARCHIVAL CANDIDATES (Data > 2 Years Old)")
        report.append("-" * 80)
        archival = self.get_archival_candidates(730)
        for table_name, data in archival.items():
            if 'error' in data:
                report.append(f"{table_name}: Error - {data['error']}")
            else:
                report.append(f"{table_name}:")
                report.append(f"  Rows to Archive: {data['rows_to_archive']:,}")
                report.append(f"  Date Range: {data['oldest_date']} to {data['newest_date']}")
        report.append("")
        
        # Recommendations
        report.append("💡 RECOMMENDATIONS")
        report.append("-" * 80)
        
        if partition_stats['missing_partition'] > 0:
            report.append("⚠️  Add partition filters to queries missing them")
            report.append("   - Always filter on processed_at, created_at, or timestamp columns")
        
        if total_cost > 100:
            report.append("⚠️  High weekly costs detected")
            report.append("   - Review expensive queries and optimize")
            report.append("   - Consider using materialized views for common aggregations")
        
        total_archival = sum(d.get('rows_to_archive', 0) for d in archival.values())
        if total_archival > 1000000:
            report.append("⚠️  Large amount of data eligible for archival")
            report.append(f"   - {total_archival:,} rows can be archived to reduce costs")
            report.append("   - Run: ./data_archival.sh to set up automated archival")
        
        report.append("")
        report.append("=" * 80)
        
        return "\n".join(report)


def main():
    parser = argparse.ArgumentParser(description='Monitor BigQuery optimization')
    parser.add_argument('--project-id', required=True, help='GCP Project ID')
    parser.add_argument('--output', help='Output file for report (default: stdout)')
    
    args = parser.parse_args()
    
    monitor = BigQueryOptimizationMonitor(args.project_id)
    report = monitor.generate_report()
    
    if args.output:
        with open(args.output, 'w') as f:
            f.write(report)
        print(f"Report written to {args.output}")
    else:
        print(report)


if __name__ == '__main__':
    main()
