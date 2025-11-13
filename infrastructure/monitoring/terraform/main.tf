# Terraform configuration for database monitoring infrastructure

terraform {
  required_version = ">= 1.0"
  required_providers {
    google = {
      source  = "hashicorp/google"
      version = "~> 5.0"
    }
  }
}

variable "project_id" {
  description = "GCP project ID"
  type        = string
}

variable "alert_email" {
  description = "Email address for alert notifications"
  type        = string
}

variable "region" {
  description = "GCP region"
  type        = string
  default     = "us-central1"
}

provider "google" {
  project = var.project_id
  region  = var.region
}

# Notification channel for email alerts
resource "google_monitoring_notification_channel" "database_alerts_email" {
  display_name = "Database Alerts Email"
  type         = "email"
  
  labels = {
    email_address = var.alert_email
  }
  
  enabled = true
}

# Alert policy for high query latency
resource "google_monitoring_alert_policy" "high_query_latency" {
  display_name = "Database - High Query Latency"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Average query time > 200ms"
    
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/database/average_query_time_ms\" resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 200
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.database_alerts_email.id]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  documentation {
    content   = <<-EOT
      ## High Query Latency Alert
      
      Average database query latency has exceeded 200ms threshold.
      
      ### Investigation Steps
      1. Check Cloud SQL CPU and memory utilization
      2. Review slow query log in Cloud SQL
      3. Check connection pool metrics
      4. Review recent database schema changes
      
      ### Resolution
      - Optimize slow queries with proper indexes
      - Increase Cloud SQL instance size if needed
      - Review and optimize connection pool settings
    EOT
    mime_type = "text/markdown"
  }
}

# Alert policy for high slow query rate
resource "google_monitoring_alert_policy" "high_slow_query_rate" {
  display_name = "Database - High Slow Query Rate"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Slow query percentage > 5%"
    
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/database/slow_query_percentage\" resource.type=\"cloud_run_revision\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 5.0
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.database_alerts_email.id]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  documentation {
    content   = <<-EOT
      ## High Slow Query Rate Alert
      
      More than 5% of queries are taking longer than 200ms to execute.
      
      ### Investigation Steps
      1. Check slow query log for patterns
      2. Review Cloud SQL performance insights
      3. Check for missing indexes
      
      ### Resolution
      - Add indexes for frequently queried columns
      - Optimize N+1 query patterns
      - Implement query result caching
    EOT
    mime_type = "text/markdown"
  }
}

# Alert policy for connection pool near capacity
resource "google_monitoring_alert_policy" "connection_pool_capacity" {
  display_name = "Database - Connection Pool Near Capacity"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Connection pool utilization > 90%"
    
    condition_threshold {
      filter          = "metric.type=\"custom.googleapis.com/database/connection_pool_checked_out\" resource.type=\"cloud_run_revision\""
      duration        = "180s"
      comparison      = "COMPARISON_GT"
      threshold_value = 18  # 90% of default pool size (20)
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.database_alerts_email.id]
  
  alert_strategy {
    auto_close = "900s"
  }
  
  documentation {
    content   = <<-EOT
      ## Connection Pool Near Capacity Alert
      
      Database connection pool is near maximum capacity (>90% utilization).
      
      ### Investigation Steps
      1. Check connection pool metrics
      2. Review application logs for connection leaks
      3. Check for long-running transactions
      
      ### Resolution
      - Increase connection pool size if within Cloud SQL limits
      - Fix connection leaks in application code
      - Optimize transaction duration
    EOT
    mime_type = "text/markdown"
  }
}

# Alert policy for high Cloud SQL CPU
resource "google_monitoring_alert_policy" "cloudsql_high_cpu" {
  display_name = "Cloud SQL - High CPU Utilization"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "CPU utilization > 80%"
    
    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/cpu/utilization\" resource.type=\"cloudsql_database\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.database_alerts_email.id]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  documentation {
    content   = <<-EOT
      ## Cloud SQL High CPU Alert
      
      Cloud SQL instance CPU utilization has exceeded 80%.
      
      ### Investigation Steps
      1. Check Cloud SQL Performance Insights
      2. Review slow query log
      3. Check for missing indexes
      
      ### Resolution
      - Optimize expensive queries
      - Add appropriate indexes
      - Consider upgrading Cloud SQL instance size
    EOT
    mime_type = "text/markdown"
  }
}

# Alert policy for high Cloud SQL memory
resource "google_monitoring_alert_policy" "cloudsql_high_memory" {
  display_name = "Cloud SQL - High Memory Utilization"
  combiner     = "OR"
  enabled      = true
  
  conditions {
    display_name = "Memory utilization > 80%"
    
    condition_threshold {
      filter          = "metric.type=\"cloudsql.googleapis.com/database/memory/utilization\" resource.type=\"cloudsql_database\""
      duration        = "300s"
      comparison      = "COMPARISON_GT"
      threshold_value = 0.8
      
      aggregations {
        alignment_period   = "60s"
        per_series_aligner = "ALIGN_MEAN"
      }
    }
  }
  
  notification_channels = [google_monitoring_notification_channel.database_alerts_email.id]
  
  alert_strategy {
    auto_close = "1800s"
  }
  
  documentation {
    content   = <<-EOT
      ## Cloud SQL High Memory Alert
      
      Cloud SQL instance memory utilization has exceeded 80%.
      
      ### Investigation Steps
      1. Check Cloud SQL memory usage breakdown
      2. Review connection count and pool settings
      3. Check for memory leaks
      
      ### Resolution
      - Optimize queries to reduce memory usage
      - Reduce connection pool size if excessive
      - Consider upgrading Cloud SQL instance size
    EOT
    mime_type = "text/markdown"
  }
}

# Outputs
output "notification_channel_id" {
  description = "ID of the notification channel"
  value       = google_monitoring_notification_channel.database_alerts_email.id
}

output "alert_policy_ids" {
  description = "IDs of created alert policies"
  value = {
    high_query_latency      = google_monitoring_alert_policy.high_query_latency.id
    high_slow_query_rate    = google_monitoring_alert_policy.high_slow_query_rate.id
    connection_pool_capacity = google_monitoring_alert_policy.connection_pool_capacity.id
    cloudsql_high_cpu       = google_monitoring_alert_policy.cloudsql_high_cpu.id
    cloudsql_high_memory    = google_monitoring_alert_policy.cloudsql_high_memory.id
  }
}
