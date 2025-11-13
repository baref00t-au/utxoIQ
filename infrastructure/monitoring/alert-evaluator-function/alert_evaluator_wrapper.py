"""
Alert evaluator wrapper for Cloud Function.

This module provides a simplified wrapper around the AlertEvaluator
that can be used in the Cloud Function context.
"""
import logging
from datetime import datetime, timedelta
from typing import List, Optional, Dict, Any
from sqlalchemy import select, and_
from sqlalchemy.ext.asyncio import AsyncSession

logger = logging.getLogger(__name__)


class AlertEvaluatorWrapper:
    """Wrapper for AlertEvaluator compatible with Cloud Function."""
    
    def __init__(
        self,
        metrics_service: Any,
        db: AsyncSession,
        notification_service: Optional[Any] = None
    ):
        """
        Initialize alert evaluator wrapper.
        
        Args:
            metrics_service: Service for querying metrics
            db: Database session
            notification_service: Optional service for sending notifications
        """
        self.metrics = metrics_service
        self.db = db
        self.notifications = notification_service
        
        logger.info("AlertEvaluatorWrapper initialized")
    
    async def evaluate_all_alerts(self) -> Dict[str, Any]:
        """
        Evaluate all enabled alert configurations.
        
        Returns:
            Dictionary with evaluation summary
        """
        # Import models here to avoid import issues
        from models import AlertConfiguration, AlertHistory
        
        logger.info("Starting evaluation of all enabled alerts")
        
        summary = {
            "total_evaluated": 0,
            "triggered": 0,
            "resolved": 0,
            "suppressed": 0,
            "errors": 0
        }
        
        # Get all enabled alerts
        stmt = select(AlertConfiguration).where(
            AlertConfiguration.enabled == True  # noqa: E712
        )
        result = await self.db.execute(stmt)
        configs = result.scalars().all()
        
        summary["total_evaluated"] = len(configs)
        logger.info(f"Found {len(configs)} enabled alert configurations")
        
        # Evaluate each alert
        for config in configs:
            try:
                result = await self._evaluate_alert(config, AlertHistory)
                
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
    
    async def _evaluate_alert(
        self,
        config: Any,
        AlertHistory: Any
    ) -> Dict[str, Any]:
        """Evaluate a single alert configuration."""
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
            return result
        
        # Get current metric value
        try:
            metric_value = await self._get_current_metric_value(
                config.service_name,
                config.metric_type,
                config.evaluation_window_seconds
            )
            result["metric_value"] = metric_value
            
        except Exception as e:
            logger.warning(f"Metric not found for alert {config.id}: {e}")
            return result
        
        # Evaluate threshold
        triggered = self._evaluate_threshold(
            metric_value,
            config.threshold_value,
            config.comparison_operator
        )
        
        if triggered:
            was_triggered = await self._handle_alert_triggered(
                config, metric_value, AlertHistory
            )
            result["triggered"] = was_triggered
        else:
            was_resolved = await self._handle_alert_resolved(config, AlertHistory)
            result["resolved"] = was_resolved
        
        return result
    
    def _evaluate_threshold(
        self,
        value: float,
        threshold: float,
        operator: str
    ) -> bool:
        """Evaluate if value crosses threshold."""
        operators = {
            '>': lambda v, t: v > t,
            '<': lambda v, t: v < t,
            '>=': lambda v, t: v >= t,
            '<=': lambda v, t: v <= t,
            '==': lambda v, t: abs(v - t) < 0.001,
        }
        
        if operator not in operators:
            logger.error(f"Invalid comparison operator: {operator}")
            return False
        
        result = operators[operator](value, threshold)
        logger.debug(f"Threshold evaluation: {value} {operator} {threshold} = {result}")
        
        return result
    
    async def _handle_alert_triggered(
        self,
        config: Any,
        metric_value: float,
        AlertHistory: Any
    ) -> bool:
        """Handle alert trigger."""
        # Check if already triggered
        stmt = select(AlertHistory).where(
            and_(
                AlertHistory.alert_config_id == config.id,
                AlertHistory.resolved_at.is_(None)
            )
        ).order_by(AlertHistory.triggered_at.desc())
        
        result = await self.db.execute(stmt)
        existing = result.scalars().first()
        
        if existing:
            logger.debug(f"Alert {config.id} already active")
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
            f"Alert triggered: {config.name} (id={config.id}) - "
            f"{metric_value} {config.comparison_operator} {config.threshold_value}"
        )
        
        # Send notifications
        if self.notifications:
            await self._send_notifications(config, alert)
        
        return True
    
    async def _handle_alert_resolved(self, config: Any, AlertHistory: Any) -> bool:
        """Handle alert resolution."""
        # Check for active alert
        stmt = select(AlertHistory).where(
            and_(
                AlertHistory.alert_config_id == config.id,
                AlertHistory.resolved_at.is_(None)
            )
        ).order_by(AlertHistory.triggered_at.desc())
        
        result = await self.db.execute(stmt)
        active_alert = result.scalars().first()
        
        if not active_alert:
            return False
        
        # Update alert history
        active_alert.resolved_at = datetime.utcnow()
        active_alert.resolution_method = 'auto'
        
        await self.db.commit()
        
        logger.info(f"Alert resolved: {config.name} (id={config.id})")
        
        # Send resolution notification
        if self.notifications:
            await self._send_resolution_notification(config, active_alert)
        
        return True
    
    def _is_suppressed(self, config: Any) -> bool:
        """Check if alert is currently suppressed."""
        if not config.suppression_enabled:
            return False
        
        if config.suppression_start is None or config.suppression_end is None:
            return False
        
        now = datetime.utcnow()
        return config.suppression_start <= now <= config.suppression_end
    
    async def _get_current_metric_value(
        self,
        service_name: str,
        metric_type: str,
        evaluation_window_seconds: int
    ) -> float:
        """Get current metric value for evaluation."""
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
            raise Exception(f"No data found for metric {metric_type}")
        
        latest_point = time_series[0]['points'][-1]
        return latest_point['value']
    
    def _format_alert_message(self, config: Any, metric_value: float) -> str:
        """Format alert message."""
        message = (
            f"{config.service_name} - {config.metric_type}: "
            f"{metric_value:.2f} {config.comparison_operator} {config.threshold_value:.2f}"
        )
        
        if config.threshold_type == 'percentage':
            message += " (percentage threshold)"
        elif config.threshold_type == 'rate':
            message += " (rate of change threshold)"
        
        return message
    
    async def _send_notifications(self, config: Any, alert: Any) -> None:
        """Send alert notifications."""
        if not config.notification_channels:
            return
        
        notification_success = False
        
        for channel in config.notification_channels:
            try:
                if channel == 'email':
                    await self.notifications.send_email_alert(config, alert)
                    notification_success = True
                elif channel == 'slack':
                    await self.notifications.send_slack_alert(config, alert)
                    notification_success = True
                elif channel == 'sms' and config.severity == 'critical':
                    await self.notifications.send_sms_alert(config, alert)
                    notification_success = True
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")
        
        if notification_success:
            alert.notification_sent = True
            await self.db.commit()
    
    async def _send_resolution_notification(self, config: Any, alert: Any) -> None:
        """Send resolution notification."""
        if not config.notification_channels:
            return
        
        for channel in config.notification_channels:
            try:
                if channel == 'email':
                    await self.notifications.send_email_resolution(config, alert)
                elif channel == 'slack':
                    await self.notifications.send_slack_resolution(config, alert)
            except Exception as e:
                logger.error(f"Failed to send {channel} resolution: {e}")


# Import Any type
from typing import Any  # noqa: E402
