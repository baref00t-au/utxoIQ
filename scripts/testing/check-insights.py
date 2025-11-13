from google.cloud import bigquery

client = bigquery.Client(project='utxoiq-dev')
query = 'SELECT COUNT(*) as count FROM intel.insights'
result = list(client.query(query).result())
print(f'Insights count: {result[0]["count"]}')

# Show sample
query2 = 'SELECT insight_id, signal_type, headline FROM intel.insights LIMIT 3'
results = list(client.query(query2).result())
print('\nSample insights:')
for row in results:
    print(f'  - [{row["signal_type"]}] {row["headline"][:60]}...')
