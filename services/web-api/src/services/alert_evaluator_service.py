"""
Alert evaluation engine for monitoring and alerting system.

This service evaluates alert configurations against current metrics,
triggers alerts when thresholds are exceeded, and handles alert resolution.
"""
import logging
from datetime import datetime
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

from src.models.monitoring import AlertConfiguration, AlertHistory
from src.services.metrics_service import MetricsService

logger = logging.getLogger(__name__)


class AlertEvaluationError(Exception):
    """Base exception for alert evaluation errors."""
    pass


class MetricNotFoundError(AlertEvaluationError):
    """Raised when a metric cannot be found or queried."""
    pass


class AlertEvaluator:
    """
    Alert evaluation engine that checks alert configurations against current metrics.
    
    This class handles:
    - Evaluating all enabled alerts
    - Checking thresholds with various comparison operators
    - Triggering alerts when thresholds are exceeded
    - Resolving alerts when conditions clear
    - Suppressing alerts during maintenance windows
    """
    
    def __init__(
        self,
        metrics_service: MetricsService,
        db: AsyncSession,
        notification_service: Optional[Any] = None
    ):
        """
        Initialize alert evaluator.
        
        Args:
            metrics_service: Service for querying metrics
            db: Database session
            notification_service: Optional service for sending notifications
        """
        self.metrics = metrics_service
        self.db = db
        self.notifications = notification_service
        
        logger.info("AlertEvaluator initialized")
    
    async def evaluate_all_alerts(self) -> Dict[str, Any]:
        """
        Evaluate all enabled alert configurations.
        
        Returns:
            Dictionary with evaluation summary:
            - total_evaluated: Number of alerts evaluated
            - triggered: Number of alerts triggered
            - resolved: Number of alerts resolved
            - suppressed: Number of alerts suppressed
            - errors: Number of evaluation errors
        """
        logger.info("Starting evaluation of all enabled alerts")
        
        summary = {
            "total_evaluated": 0,
            "triggered": 0,
            "resolved": 0,
            "suppressed": 0,
            "errors": 0
        }
        
        # Get all enabled alerts
        configs = await self._get_enabled_alerts()
        summary["total_evaluated"] = len(configs)
        
        logger.info(f"Found {len(configs)} enabled alert configurations")
        
        # Evaluate each alert
        for config in configs:
            try:
                result = await self.evaluate_alert(config)
                
                if result["suppressed"]:
                    summary["suppressed"] += 1
                elif result["triggered"]:
                    summary["triggered"] += 1
                elif result["resolved"]:
                    summary["resolved"] += 1
                    
            except Exception as e:
                summary["errors"] += 1
                logger.error(
                    f"Error evaluating alert {config.id} ({config.name}): {e}",
                    exc_info=True
                )
        
        logger.info(
            f"Alert evaluation complete: {summary['triggered']} triggered, "
            f"{summary['resolved']} resolved, {summary['suppressed']} suppressed, "
            f"{summary['errors']} errors"
        )
        
        return summary
    
    async def evaluate_alert(self, config: AlertConfiguration) -> Dict[str, Any]:
        """
        Evaluate a single alert configuration.
        
        Args:
            config: Alert configuration to evaluate
            
        Returns:
            Dictionary with evaluation result:
            - suppressed: Whether alert was suppressed
            - triggered: Whether alert was triggered
            - resolved: Whether alert was resolved
            - metric_value: Current metric value (if available)
        """
        logger.debug(f"Evaluating alert {config.id} ({config.name})")
        
        result = {
            "suppressed": False,
            "triggered": False,
            "resolved": False,
            "metric_value": None
        }
        
        # Check if suppressed
        if self._is_suppressed(config):
            logger.debug(f"Alert {config.id} is suppressed")
            result["suppressed"] = True
            await self._log_suppressed_alert(config)
            return result
        
        # Get current metric value
        try:
            metric_value = await self._get_current_metric_value(
                config.service_name,
                config.metric_type,
                config.evaluation_window_seconds
            )
            result["metric_value"] = metric_value
            
        except MetricNotFoundError as e:
            logger.warning(f"Metric not found for alert {config.id}: {e}")
            # If metric is not found, we can't evaluate, so skip
            return result
        
        # Evaluate threshold
        triggered = self._evaluate_threshold(
            metric_value,
            config.threshold_value,
            config.comparison_operator
        )
        
        if triggered:
            # Handle alert trigger
            was_triggered = await self._handle_alert_triggered(config, metric_value)
            result["triggered"] = was_triggered
        else:
            # Handle alert resolution
            was_resolved = await self._handle_alert_resolved(config)
            result["resolved"] = was_resolved
        
        return result
    
    def _evaluate_threshold(
        self,
        value: float,
        threshold: float,
        operator: str
    ) -> bool:
        """
        Evaluate if value crosses threshold using the specified operator.
        
        Args:
            value: Current metric value
            threshold: Threshold value to compare against
            operator: Comparison operator ('>', '<', '>=', '<=', '==')
            
        Returns:
            True if threshold is crossed, False otherwise
        """
        operators = {
            '>': lambda v, t: v > t,
            '<': lambda v, t: v < t,
            '>=': lambda v, t: v >= t,
            '<=': lambda v, t: v <= t,
            '==': lambda v, t: abs(v - t) < 0.001,  # Floating point comparison
        }
        
        if operator not in operators:
            logger.error(f"Invalid comparison operator: {operator}")
            return False
        
        result = operators[operator](value, threshold)
        
        logger.debug(
            f"Threshold evaluation: {value} {operator} {threshold} = {result}"
        )
        
        return result
    
    async def _handle_alert_triggered(
        self,
        config: AlertConfiguration,
        metric_value: float
    ) -> bool:
        """
        Handle alert trigger by creating history record and sending notifications.
        
        Args:
            config: Alert configuration
            metric_value: Current metric value that triggered the alert
            
        Returns:
            True if alert was newly triggered, False if already active
        """
        # Check if already triggered (active alert exists)
        existing = await self._get_active_alert(config.id)
        if existing:
            logger.debug(
                f"Alert {config.id} already active (history_id={existing.id})"
            )
            return False
        
        # Create alert history record
        alert = AlertHistory(
            alert_config_id=config.id,
            triggered_at=datetime.utcnow(),
            severity=config.severity,
            metric_value=metric_value,
            threshold_value=config.threshold_value,
            message=self._format_alert_message(config, metric_value),
            notification_sent=False,
            notification_channels=config.notification_channels
        )
        
        self.db.add(alert)
        await self.db.commit()
        await self.db.refresh(alert)
        
        logger.info(
            f"Alert triggered: {config.name} (id={config.id}, history_id={alert.id}) - "
            f"{metric_value} {config.comparison_operator} {config.threshold_value}"
        )
        
        # Send notifications
        if self.notifications:
            await self._send_notifications(config, alert)
        else:
            logger.warning(
                f"Notification service not configured, skipping notifications for alert {config.id}"
            )
        
        return True
    
    async def _handle_alert_resolved(self, config: AlertConfiguration) -> bool:
        """
        Handle alert resolution by updating history record.
        
        Args:
            config: Alert configuration
            
        Returns:
            True if alert was resolved, False if no active alert
        """
        # Check for active alert
        active_alert = await self._get_active_alert(config.id)
        if not active_alert:
            # No active alert to resolve
            return False
        
        # Update alert history with resolution
        active_alert.resolved_at = datetime.utcnow()
        active_alert.resolution_method = 'auto'
        
        await self.db.commit()
        
        logger.info(
            f"Alert resolved: {config.name} (id={config.id}, history_id={active_alert.id})"
        )
        
        # Send resolution notification
        if self.notifications:
            await self._send_resolution_notification(config, active_alert)
        
        return True
    
    def _is_suppressed(self, config: AlertConfiguration) -> bool:
        """
        Check if alert is currently suppressed.
        
        Args:
            config: Alert configuration
            
        Returns:
            True if alert is suppressed, False otherwise
        """
        if not config.suppression_enabled:
            return False
        
        if config.suppression_start is None or config.suppression_end is None:
            return False
        
        now = datetime.utcnow()
        
        # Check if current time is within suppression window
        is_suppressed = config.suppression_start <= now <= config.suppression_end
        
        return is_suppressed
    
    async def _log_suppressed_alert(self, config: AlertConfiguration) -> None:
        """
        Log suppressed alert for audit purposes.
        
        Args:
            config: Alert configuration that was suppressed
        """
        logger.info(
            f"Alert suppressed: {config.name} (id={config.id}) - "
            f"suppression window: {config.suppression_start} to {config.suppression_end}"
        )
    
    async def _get_enabled_alerts(self) -> List[AlertConfiguration]:
        """
        Get all enabled alert configurations from database.
        
        Returns:
            List of enabled alert configurations
        """
        stmt = select(AlertConfiguration).where(
            AlertConfiguration.enabled == True  # noqa: E712
        )
        result = await self.db.execute(stmt)
        configs = result.scalars().all()
        
        return list(configs)
    
    async def _get_active_alert(
        self,
        alert_config_id: Any
    ) -> Optional[AlertHistory]:
        """
        Get active (unresolved) alert for a configuration.
        
        Args:
            alert_config_id: Alert configuration ID
            
        Returns:
            Active AlertHistory record or None
        """
        stmt = select(AlertHistory).where(
            and_(
                AlertHistory.alert_config_id == alert_config_id,
                AlertHistory.resolved_at.is_(None)
            )
        ).order_by(AlertHistory.triggered_at.desc())
        
        result = await self.db.execute(stmt)
        active_alert = result.scalars().first()
        
        return active_alert
    
    async def _get_current_metric_value(
        self,
        service_name: str,
        metric_type: str,
        evaluation_window_seconds: int
    ) -> float:
        """
        Get current metric value for evaluation.
        
        Args:
            service_name: Service name
            metric_type: Metric type
            evaluation_window_seconds: Time window for metric aggregation
            
        Returns:
            Current metric value (aggregated over evaluation window)
            
        Raises:
            MetricNotFoundError: If metric cannot be queried
        """
        try:
            # Convert evaluation window to time range string
            minutes = evaluation_window_seconds // 60
            if minutes < 60:
                time_range = f"{minutes}m" if minutes > 0 else "5m"
            else:
                hours = minutes // 60
                time_range = f"{hours}h"
            
            # Query metric
            metric_full_type = f"custom.googleapis.com/{service_name}/{metric_type}"
            end_time = datetime.utcnow()
            start_time = end_time - timedelta(seconds=evaluation_window_seconds)
            
            time_series = await self.metrics.get_time_series(
                metric_type=metric_full_type,
                start_time=start_time,
                end_time=end_time,
                aggregation="ALIGN_MEAN",
                interval_seconds=evaluation_window_seconds,
                resource_labels={"service_name": service_name}
            )
            
            if not time_series or not time_series[0]['points']:
                raise MetricNotFoundError(
                    f"No data found for metric {metric_type} on service {service_name}"
                )
            
            # Get the most recent value
            latest_point = time_series[0]['points'][-1]
            value = latest_point['value']
            
            logger.debug(
                f"Retrieved metric value: {service_name}/{metric_type} = {value}"
            )
            
            return value
            
        except Exception as e:
            logger.error(
                f"Error getting metric value for {service_name}/{metric_type}: {e}"
            )
            raise MetricNotFoundError(
                f"Failed to query metric {metric_type} for {service_name}: {e}"
            ) from e
    
    def _format_alert_message(
        self,
        config: AlertConfiguration,
        metric_value: float
    ) -> str:
        """
        Format alert message with metric details.
        
        Args:
            config: Alert configuration
            metric_value: Current metric value
            
        Returns:
            Formatted alert message
        """
        message = (
            f"{config.service_name} - {config.metric_type}: "
            f"{metric_value:.2f} {config.comparison_operator} {config.threshold_value:.2f}"
        )
        
        # Add context based on threshold type
        if config.threshold_type == 'percentage':
            message += " (percentage threshold)"
        elif config.threshold_type == 'rate':
            message += " (rate of change threshold)"
        
        return message
    
    async def _send_notifications(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> None:
        """
        Send alert notifications to configured channels.
        
        Args:
            config: Alert configuration
            alert: Alert history record
        """
        if not config.notification_channels:
            logger.debug(f"No notification channels configured for alert {config.id}")
            return
        
        notification_success = False
        
        for channel in config.notification_channels:
            try:
                if channel == 'email':
                    await self.notifications.send_email_alert(config, alert)
                    notification_success = True
                    logger.info(f"Email notification sent for alert {config.id}")
                    
                elif channel == 'slack':
                    await self.notifications.send_slack_alert(config, alert)
                    notification_success = True
                    logger.info(f"Slack notification sent for alert {config.id}")
                    
                elif channel == 'sms' and config.severity == 'critical':
                    await self.notifications.send_sms_alert(config, alert)
                    notification_success = True
                    logger.info(f"SMS notification sent for alert {config.id}")
                    
                elif channel == 'sms':
                    logger.debug(
                        f"Skipping SMS notification for non-critical alert {config.id}"
                    )
                    
            except Exception as e:
                logger.error(
                    f"Failed to send {channel} notification for alert {config.id}: {e}",
                    exc_info=True
                )
        
        # Update notification status
        if notification_success:
            alert.notification_sent = True
            await self.db.commit()
    
    async def _send_resolution_notification(
        self,
        config: AlertConfiguration,
        alert: AlertHistory
    ) -> None:
        """
        Send resolution notification when alert clears.
        
        Args:
            config: Alert configuration
            alert: Resolved alert history record
        """
        if not config.notification_channels:
            return
        
        for channel in config.notification_channels:
            try:
                if channel == 'email':
                    await self.notifications.send_email_resolution(config, alert)
                    logger.info(f"Email resolution notification sent for alert {config.id}")
                    
                elif channel == 'slack':
                    await self.notifications.send_slack_resolution(config, alert)
                    logger.info(f"Slack resolution notification sent for alert {config.id}")
                    
                # Note: SMS resolution notifications are typically not sent
                # to avoid notification fatigue
                    
            except Exception as e:
                logger.error(
                    f"Failed to send {channel} resolution notification for alert {config.id}: {e}",
                    exc_info=True
                )


# Import timedelta here to avoid circular import
from datetime import timedelta  # noqa: E402
