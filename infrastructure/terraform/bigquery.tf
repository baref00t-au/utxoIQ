# BigQuery resources for hybrid dataset approach

resource "google_bigquery_dataset" "btc" {
  dataset_id                  = "btc"
  project                     = var.project_id
  location                    = var.region
  description                 = "Bitcoin blockchain data (real-time 24h buffer)"
  default_table_expiration_ms = null

  labels = {
    environment = var.environment
    service     = "utxoiq"
  }
}

# Blocks table
resource "google_bigquery_table" "blocks" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "blocks"
  project    = var.project_id

  description = "Bitcoin blocks (last 24 hours)"

  time_partitioning {
    type  = "DAY"
    field = "timestamp"
  }

  clustering = ["number", "hash"]

  schema = file("${path.module}/../bigquery/schemas/blocks.json")
}

# Transactions table
resource "google_bigquery_table" "transactions" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "transactions"
  project    = var.project_id

  description = "Bitcoin transactions (last 24 hours)"

  time_partitioning {
    type  = "DAY"
    field = "block_timestamp"
  }

  clustering = ["block_number", "hash"]

  schema = file("${path.module}/../bigquery/schemas/transactions.json")
}

# Inputs table
resource "google_bigquery_table" "inputs" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "inputs"
  project    = var.project_id

  description = "Bitcoin transaction inputs (last 24 hours)"

  time_partitioning {
    type  = "DAY"
    field = "block_timestamp"
  }

  clustering = ["transaction_hash"]

  schema = file("${path.module}/../bigquery/schemas/inputs.json")
}

# Outputs table
resource "google_bigquery_table" "outputs" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "outputs"
  project    = var.project_id

  description = "Bitcoin transaction outputs (last 24 hours)"

  time_partitioning {
    type  = "DAY"
    field = "block_timestamp"
  }

  clustering = ["transaction_hash"]

  schema = file("${path.module}/../bigquery/schemas/outputs.json")
}

# Unified views
resource "google_bigquery_table" "blocks_unified" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "blocks_unified"
  project    = var.project_id

  description = "Unified view combining public and custom block data"

  view {
    query = <<-SQL
      SELECT * FROM `bigquery-public-data.crypto_bitcoin.blocks`
      WHERE timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      UNION ALL
      SELECT * FROM `${var.project_id}.${google_bigquery_dataset.btc.dataset_id}.blocks`
      WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    SQL

    use_legacy_sql = false
  }
}

resource "google_bigquery_table" "transactions_unified" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "transactions_unified"
  project    = var.project_id

  description = "Unified view combining public and custom transaction data"

  view {
    query = <<-SQL
      SELECT * FROM `bigquery-public-data.crypto_bitcoin.transactions`
      WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      UNION ALL
      SELECT * FROM `${var.project_id}.${google_bigquery_dataset.btc.dataset_id}.transactions`
      WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    SQL

    use_legacy_sql = false
  }
}

resource "google_bigquery_table" "inputs_unified" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "inputs_unified"
  project    = var.project_id

  description = "Unified view combining public and custom input data"

  view {
    query = <<-SQL
      SELECT * FROM `bigquery-public-data.crypto_bitcoin.inputs`
      WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      UNION ALL
      SELECT * FROM `${var.project_id}.${google_bigquery_dataset.btc.dataset_id}.inputs`
      WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    SQL

    use_legacy_sql = false
  }
}

resource "google_bigquery_table" "outputs_unified" {
  dataset_id = google_bigquery_dataset.btc.dataset_id
  table_id   = "outputs_unified"
  project    = var.project_id

  description = "Unified view combining public and custom output data"

  view {
    query = <<-SQL
      SELECT * FROM `bigquery-public-data.crypto_bitcoin.outputs`
      WHERE block_timestamp < TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
      UNION ALL
      SELECT * FROM `${var.project_id}.${google_bigquery_dataset.btc.dataset_id}.outputs`
      WHERE block_timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL 24 HOUR)
    SQL

    use_legacy_sql = false
  }
}

# Cloud Scheduler job for cleanup
resource "google_cloud_scheduler_job" "bigquery_cleanup" {
  name             = "bigquery-cleanup"
  description      = "Clean up old data from custom BigQuery dataset"
  schedule         = "0 */6 * * *"  # Every 6 hours
  time_zone        = "UTC"
  attempt_deadline = "320s"
  project          = var.project_id
  region           = var.region

  http_target {
    http_method = "POST"
    uri         = "${google_cloud_run_service.feature_engine.status[0].url}/cleanup"

    oidc_token {
      service_account_email = google_service_account.feature_engine.email
    }
  }
}
