/**
 * Cloud Logging configuration for audit logs
 * 
 * This configuration sets up:
 * - Log retention policy for audit logs (1 year)
 * - Log sink for long-term storage in Cloud Storage
 * - Log-based metrics for monitoring
 */

# Log bucket for audit logs with 1-year retention
resource "google_logging_project_bucket_config" "audit_logs" {
  project        = var.project_id
  location       = var.region
  retention_days = 365  # 1 year retention as per requirement
  bucket_id      = "audit-logs"
  description    = "Audit logs for authentication and authorization events"
  
  # Enable analytics for querying
  enable_analytics = true
}

# Log sink to export audit logs to Cloud Storage for long-term archival
resource "google_logging_project_sink" "audit_logs_storage" {
  name        = "audit-logs-storage-sink"
  description = "Export audit logs to Cloud Storage for long-term retention"
  
  # Destination: Cloud Storage bucket
  destination = "storage.googleapis.com/${google_storage_bucket.audit_logs_archive.name}"
  
  # Filter for audit events
  filter = <<-EOT
    logName="projects/${var.project_id}/logs/audit"
    OR (
      jsonPayload.event_type="successful_login"
      OR jsonPayload.event_type="failed_login"
      OR jsonPayload.event_type="api_key_created"
      OR jsonPayload.event_type="api_key_revoked"
      OR jsonPayload.event_type="role_change"
      OR jsonPayload.event_type="subscription_tier_change"
      OR jsonPayload.event_type="authorization_failure"
      OR jsonPayload.event_type="api_key_scope_failure"
    )
  EOT
  
  # Use unique writer identity for the sink
  unique_writer_identity = true
}

# Cloud Storage bucket for long-term audit log archival
resource "google_storage_bucket" "audit_logs_archive" {
  name          = "${var.project_id}-audit-logs-archive"
  location      = var.region
  storage_class = "NEARLINE"  # Cost-effective for infrequent access
  
  # Lifecycle rule to transition to Archive storage after 90 days
  lifecycle_rule {
    condition {
      age = 90
    }
    action {
      type          = "SetStorageClass"
      storage_class = "ARCHIVE"
    }
  }
  
  # Lifecycle rule to delete after 7 years (compliance requirement)
  lifecycle_rule {
    condition {
      age = 2555  # 7 years in days
    }
    action {
      type = "Delete"
    }
  }
  
  # Enable versioning for audit trail
  versioning {
    enabled = true
  }
  
  # Uniform bucket-level access
  uniform_bucket_level_access {
    enabled = true
  }
  
  labels = {
    purpose     = "audit-logs"
    compliance  = "security"
    environment = var.environment
  }
}

# Grant the log sink permission to write to the bucket
resource "google_storage_bucket_iam_member" "audit_logs_sink_writer" {
  bucket = google_storage_bucket.audit_logs_archive.name
  role   = "roles/storage.objectCreator"
  member = google_logging_project_sink.audit_logs_storage.writer_identity
}

# Log-based metric for failed login attempts
resource "google_logging_metric" "failed_login_attempts" {
  name        = "failed_login_attempts"
  description = "Count of failed login attempts for security monitoring"
  
  filter = <<-EOT
    jsonPayload.event_type="failed_login"
  EOT
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    
    labels {
      key         = "reason"
      value_type  = "STRING"
      description = "Reason for login failure"
    }
    
    labels {
      key         = "auth_method"
      value_type  = "STRING"
      description = "Authentication method attempted"
    }
  }
  
  label_extractors = {
    "reason"      = "EXTRACT(jsonPayload.reason)"
    "auth_method" = "EXTRACT(jsonPayload.auth_method)"
  }
}

# Log-based metric for successful logins
resource "google_logging_metric" "successful_logins" {
  name        = "successful_logins"
  description = "Count of successful login attempts"
  
  filter = <<-EOT
    jsonPayload.event_type="successful_login"
  EOT
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    
    labels {
      key         = "auth_method"
      value_type  = "STRING"
      description = "Authentication method used"
    }
  }
  
  label_extractors = {
    "auth_method" = "EXTRACT(jsonPayload.auth_method)"
  }
}

# Log-based metric for API key events
resource "google_logging_metric" "api_key_events" {
  name        = "api_key_events"
  description = "Count of API key creation and revocation events"
  
  filter = <<-EOT
    jsonPayload.event_type="api_key_created"
    OR jsonPayload.event_type="api_key_revoked"
  EOT
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    
    labels {
      key         = "event_type"
      value_type  = "STRING"
      description = "Type of API key event"
    }
  }
  
  label_extractors = {
    "event_type" = "EXTRACT(jsonPayload.event_type)"
  }
}

# Log-based metric for authorization failures
resource "google_logging_metric" "authorization_failures" {
  name        = "authorization_failures"
  description = "Count of authorization failures for security monitoring"
  
  filter = <<-EOT
    jsonPayload.event_type="authorization_failure"
    OR jsonPayload.event_type="api_key_scope_failure"
  EOT
  
  metric_descriptor {
    metric_kind = "DELTA"
    value_type  = "INT64"
    unit        = "1"
    
    labels {
      key         = "event_type"
      value_type  = "STRING"
      description = "Type of authorization failure"
    }
    
    labels {
      key         = "user_role"
      value_type  = "STRING"
      description = "Role of the user"
    }
  }
  
  label_extractors = {
    "event_type" = "EXTRACT(jsonPayload.event_type)"
    "user_role"  = "EXTRACT(jsonPayload.user_role)"
  }
}

# Alerting policy for excessive failed login attempts
resource "google_monitoring_alert_policy" "excessive_failed_logins" {
  display_name = "Excessive Failed Login Attempts"
  combiner     = "OR"
  
  conditions {
    display_name = "Failed login rate > 10 per minute"
    
    condition_threshold {
      filter          = "metric.type=\"logging.googleapis.com/user/failed_login_attempts\" resource.type=\"global\""
      duration        = "60s"
      comparison      = "COMPARISON_GT"
      threshold_value = 10
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_RATE"
      }
    }
  }
  
  notification_channels = var.alert_notification_channels
  
  alert_strategy {
    auto_close = "1800s"  # Auto-close after 30 minutes
  }
  
  documentation {
    content   = "Excessive failed login attempts detected. This may indicate a brute force attack or credential stuffing attempt. Review audit logs for details."
    mime_type = "text/markdown"
  }
}

# Variables
variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "region" {
  description = "GCP region for resources"
  type        = string
  default     = "us-central1"
}

variable "environment" {
  description = "Environment name (dev, staging, prod)"
  type        = string
}

variable "alert_notification_channels" {
  description = "List of notification channel IDs for alerts"
  type        = list(string)
  default     = []
}

# Outputs
output "audit_logs_bucket_name" {
  description = "Name of the Cloud Storage bucket for audit log archives"
  value       = google_storage_bucket.audit_logs_archive.name
}

output "audit_logs_bucket_id" {
  description = "ID of the Cloud Logging bucket for audit logs"
  value       = google_logging_project_bucket_config.audit_logs.bucket_id
}

output "log_sink_name" {
  description = "Name of the log sink for audit logs"
  value       = google_logging_project_sink.audit_logs_storage.name
}
