# Terraform configuration for Cloud SQL backup and recovery
# This file defines the backup configuration for the PostgreSQL instance

# Cloud SQL Instance with backup configuration
resource "google_sql_database_instance" "utxoiq_postgres" {
  name             = var.instance_name
  database_version = "POSTGRES_15"
  region           = var.primary_region
  project          = var.project_id

  settings {
    tier              = "db-custom-2-7680"  # 2 vCPU, 7.5 GB RAM
    availability_type = "REGIONAL"          # High availability
    disk_type         = "PD_SSD"
    disk_size         = 100
    disk_autoresize   = true
    disk_autoresize_limit = 500

    # Backup configuration
    backup_configuration {
      enabled                        = true
      start_time                     = "01:00"  # Daily at 01:00 UTC
      point_in_time_recovery_enabled = true
      transaction_log_retention_days = 7
      
      backup_retention_settings {
        retained_backups = 7
        retention_unit   = "COUNT"
      }

      # Store backups in separate region
      location = var.backup_region
    }

    # Maintenance window
    maintenance_window {
      day          = 7  # Sunday
      hour         = 2  # 02:00 UTC
      update_track = "stable"
    }

    # IP configuration
    ip_configuration {
      ipv4_enabled    = true
      private_network = var.vpc_network
      require_ssl     = true
    }

    # Database flags
    database_flags {
      name  = "log_checkpoints"
      value = "on"
    }

    database_flags {
      name  = "log_connections"
      value = "on"
    }

    database_flags {
      name  = "log_disconnections"
      value = "on"
    }

    database_flags {
      name  = "log_lock_waits"
      value = "on"
    }

    # Insights configuration for monitoring
    insights_config {
      query_insights_enabled  = true
      query_string_length     = 1024
      record_application_tags = true
      record_client_address   = true
    }
  }

  # Deletion protection
  deletion_protection = true
}

# Cloud Storage bucket for manual backups and exports
resource "google_storage_bucket" "backup_bucket" {
  name          = var.backup_bucket_name
  location      = var.backup_region
  project       = var.project_id
  storage_class = "STANDARD"
  
  # Enable versioning
  versioning {
    enabled = true
  }

  # Lifecycle rules
  lifecycle_rule {
    condition {
      age = 7
      matches_storage_class = ["STANDARD"]
    }
    action {
      type          = "SetStorageClass"
      storage_class = "COLDLINE"
    }
  }

  lifecycle_rule {
    condition {
      age       = 30
      is_live   = false
    }
    action {
      type = "Delete"
    }
  }

  # Uniform bucket-level access
  uniform_bucket_level_access {
    enabled = true
  }
}

# IAM binding for Cloud SQL to access backup bucket
resource "google_storage_bucket_iam_member" "cloudsql_backup_access" {
  bucket = google_storage_bucket.backup_bucket.name
  role   = "roles/storage.objectAdmin"
  member = "serviceAccount:${google_sql_database_instance.utxoiq_postgres.service_account_email_address}"
}

# Cloud Scheduler job for backup verification
resource "google_cloud_scheduler_job" "backup_verification" {
  name        = "backup-verification-job"
  description = "Weekly backup verification job"
  schedule    = "0 3 * * 0"  # Sunday at 03:00 UTC
  time_zone   = "UTC"
  project     = var.project_id
  region      = var.primary_region

  http_target {
    uri         = "${var.backup_verification_endpoint}/verify"
    http_method = "POST"
    
    headers = {
      "Content-Type" = "application/json"
    }

    body = base64encode(jsonencode({
      instance_name = var.instance_name
      project_id    = var.project_id
    }))

    oidc_token {
      service_account_email = var.scheduler_service_account
    }
  }

  retry_config {
    retry_count = 3
  }
}

# Monitoring alert for backup failures
resource "google_monitoring_alert_policy" "backup_failure" {
  display_name = "Cloud SQL Backup Failure"
  project      = var.project_id
  combiner     = "OR"

  conditions {
    display_name = "Backup operation failed"
    
    condition_threshold {
      filter          = "resource.type=\"cloudsql_database\" AND resource.labels.database_id=\"${var.project_id}:${var.instance_name}\" AND metric.type=\"cloudsql.googleapis.com/database/backup/count\" AND metric.labels.state=\"FAILED\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0
      
      aggregations {
        alignment_period   = "300s"
        per_series_aligner = "ALIGN_SUM"
      }
    }
  }

  notification_channels = var.alert_notification_channels

  alert_strategy {
    auto_close = "86400s"  # 24 hours
  }

  documentation {
    content   = "Cloud SQL backup has failed. Check backup logs and verify instance health."
    mime_type = "text/markdown"
  }
}

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "instance_name" {
  description = "Cloud SQL instance name"
  type        = string
  default     = "utxoiq-postgres"
}

variable "primary_region" {
  description = "Primary region for Cloud SQL instance"
  type        = string
  default     = "us-central1"
}

variable "backup_region" {
  description = "Region for storing backups"
  type        = string
  default     = "us-east1"
}

variable "backup_bucket_name" {
  description = "Name of the backup bucket"
  type        = string
  default     = "utxoiq-backups"
}

variable "vpc_network" {
  description = "VPC network for private IP"
  type        = string
}

variable "backup_verification_endpoint" {
  description = "Endpoint for backup verification service"
  type        = string
}

variable "scheduler_service_account" {
  description = "Service account for Cloud Scheduler"
  type        = string
}

variable "alert_notification_channels" {
  description = "Notification channels for alerts"
  type        = list(string)
}

# Outputs
output "instance_connection_name" {
  description = "Connection name for Cloud SQL instance"
  value       = google_sql_database_instance.utxoiq_postgres.connection_name
}

output "backup_bucket_url" {
  description = "URL of the backup bucket"
  value       = "gs://${google_storage_bucket.backup_bucket.name}"
}

output "instance_service_account" {
  description = "Service account email for Cloud SQL instance"
  value       = google_sql_database_instance.utxoiq_postgres.service_account_email_address
}
