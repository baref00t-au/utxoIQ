"""BigQuery client for email preferences and engagement tracking."""
from google.cloud import bigquery
from typing import Optional, List
import json
from datetime import datetime

from .config import settings
from .models import EmailPreferences, EmailEngagement, EmailFrequency, SignalType, QuietHours


class BigQueryClient:
    """Client for BigQuery operations."""
    
    def __init__(self):
        """Initialize BigQuery client."""
        self.client = bigquery.Client(project=settings.gcp_project_id)
        self.dataset_id = settings.bigquery_dataset
        self._ensure_tables_exist()
    
    def _ensure_tables_exist(self):
        """Ensure required tables exist."""
        # Email preferences table
        preferences_table_id = f"{settings.gcp_project_id}.{self.dataset_id}.email_preferences"
        preferences_schema = [
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("email", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("daily_brief_enabled", "BOOLEAN", mode="REQUIRED"),
            bigquery.SchemaField("frequency", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("signal_filters_json", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("quiet_hours_json", "STRING", mode="NULLABLE"),
            bigquery.SchemaField("created_at", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("updated_at", "TIMESTAMP", mode="REQUIRED"),
        ]
        
        # Email engagement table
        engagement_table_id = f"{settings.gcp_project_id}.{self.dataset_id}.email_engagement"
        engagement_schema = [
            bigquery.SchemaField("email_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("user_id", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("event", "STRING", mode="REQUIRED"),
            bigquery.SchemaField("timestamp", "TIMESTAMP", mode="REQUIRED"),
            bigquery.SchemaField("metadata_json", "STRING", mode="NULLABLE"),
        ]
        
        # Create tables if they don't exist
        for table_id, schema in [
            (preferences_table_id, preferences_schema),
            (engagement_table_id, engagement_schema)
        ]:
            try:
                self.client.get_table(table_id)
            except Exception:
                table = bigquery.Table(table_id, schema=schema)
                self.client.create_table(table)
    
    def get_preferences(self, user_id: str) -> Optional[EmailPreferences]:
        """Get email preferences for a user."""
        query = f"""
            SELECT *
            FROM `{settings.gcp_project_id}.{self.dataset_id}.email_preferences`
            WHERE user_id = @user_id
            LIMIT 1
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", user_id)
            ]
        )
        
        results = self.client.query(query, job_config=job_config).result()
        
        for row in results:
            signal_filters = []
            if row.signal_filters_json:
                signal_filters = [SignalType(s) for s in json.loads(row.signal_filters_json)]
            
            quiet_hours = None
            if row.quiet_hours_json:
                quiet_hours_data = json.loads(row.quiet_hours_json)
                quiet_hours = QuietHours(**quiet_hours_data)
            
            return EmailPreferences(
                user_id=row.user_id,
                email=row.email,
                daily_brief_enabled=row.daily_brief_enabled,
                frequency=EmailFrequency(row.frequency),
                signal_filters=signal_filters,
                quiet_hours=quiet_hours,
                created_at=row.created_at,
                updated_at=row.updated_at
            )
        
        return None
    
    def save_preferences(self, preferences: EmailPreferences) -> None:
        """Save or update email preferences."""
        signal_filters_json = json.dumps([s.value for s in preferences.signal_filters]) if preferences.signal_filters else None
        quiet_hours_json = preferences.quiet_hours.model_dump_json() if preferences.quiet_hours else None
        
        # Use MERGE to insert or update
        query = f"""
            MERGE `{settings.gcp_project_id}.{self.dataset_id}.email_preferences` T
            USING (
                SELECT
                    @user_id AS user_id,
                    @email AS email,
                    @daily_brief_enabled AS daily_brief_enabled,
                    @frequency AS frequency,
                    @signal_filters_json AS signal_filters_json,
                    @quiet_hours_json AS quiet_hours_json,
                    @created_at AS created_at,
                    @updated_at AS updated_at
            ) S
            ON T.user_id = S.user_id
            WHEN MATCHED THEN
                UPDATE SET
                    email = S.email,
                    daily_brief_enabled = S.daily_brief_enabled,
                    frequency = S.frequency,
                    signal_filters_json = S.signal_filters_json,
                    quiet_hours_json = S.quiet_hours_json,
                    updated_at = S.updated_at
            WHEN NOT MATCHED THEN
                INSERT (user_id, email, daily_brief_enabled, frequency, signal_filters_json, quiet_hours_json, created_at, updated_at)
                VALUES (S.user_id, S.email, S.daily_brief_enabled, S.frequency, S.signal_filters_json, S.quiet_hours_json, S.created_at, S.updated_at)
        """
        
        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", preferences.user_id),
                bigquery.ScalarQueryParameter("email", "STRING", preferences.email),
                bigquery.ScalarQueryParameter("daily_brief_enabled", "BOOLEAN", preferences.daily_brief_enabled),
                bigquery.ScalarQueryParameter("frequency", "STRING", preferences.frequency.value),
                bigquery.ScalarQueryParameter("signal_filters_json", "STRING", signal_filters_json),
                bigquery.ScalarQueryParameter("quiet_hours_json", "STRING", quiet_hours_json),
                bigquery.ScalarQueryParameter("created_at", "TIMESTAMP", preferences.created_at),
                bigquery.ScalarQueryParameter("updated_at", "TIMESTAMP", preferences.updated_at),
            ]
        )
        
        self.client.query(query, job_config=job_config).result()
    
    def get_users_for_daily_brief(self) -> List[EmailPreferences]:
        """Get all users who should receive daily brief."""
        query = f"""
            SELECT *
            FROM `{settings.gcp_project_id}.{self.dataset_id}.email_preferences`
            WHERE daily_brief_enabled = TRUE
            AND frequency = 'daily'
        """
        
        results = self.client.query(query).result()
        users = []
        
        for row in results:
            signal_filters = []
            if row.signal_filters_json:
                signal_filters = [SignalType(s) for s in json.loads(row.signal_filters_json)]
            
            quiet_hours = None
            if row.quiet_hours_json:
                quiet_hours_data = json.loads(row.quiet_hours_json)
                quiet_hours = QuietHours(**quiet_hours_data)
            
            users.append(EmailPreferences(
                user_id=row.user_id,
                email=row.email,
                daily_brief_enabled=row.daily_brief_enabled,
                frequency=EmailFrequency(row.frequency),
                signal_filters=signal_filters,
                quiet_hours=quiet_hours,
                created_at=row.created_at,
                updated_at=row.updated_at
            ))
        
        return users
    
    def track_engagement(self, engagement: EmailEngagement) -> None:
        """Track email engagement event."""
        metadata_json = json.dumps(engagement.metadata) if engagement.metadata else None
        
        table_id = f"{settings.gcp_project_id}.{self.dataset_id}.email_engagement"
        rows_to_insert = [{
            "email_id": engagement.email_id,
            "user_id": engagement.user_id,
            "event": engagement.event.value,
            "timestamp": engagement.timestamp.isoformat(),
            "metadata_json": metadata_json
        }]
        
        errors = self.client.insert_rows_json(table_id, rows_to_insert)
        if errors:
            raise Exception(f"Failed to track engagement: {errors}")
    
    def get_engagement_stats(self, user_id: Optional[str] = None, days: int = 30) -> dict:
        """Get engagement statistics."""
        where_clause = f"AND user_id = '{user_id}'" if user_id else ""
        
        query = f"""
            SELECT
                event,
                COUNT(*) as count
            FROM `{settings.gcp_project_id}.{self.dataset_id}.email_engagement`
            WHERE timestamp >= TIMESTAMP_SUB(CURRENT_TIMESTAMP(), INTERVAL {days} DAY)
            {where_clause}
            GROUP BY event
        """
        
        results = self.client.query(query).result()
        stats = {}
        
        for row in results:
            stats[row.event] = row.count
        
        return stats
