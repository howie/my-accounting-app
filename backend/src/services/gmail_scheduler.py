"""Gmail scan scheduler using APScheduler.

Feature 011: Gmail CC Statement Import - US5 Scheduled Auto-Scan
"""

import logging
import uuid
from datetime import UTC, datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.cron import CronTrigger
from sqlmodel import Session, select

from src.models.gmail_connection import GmailConnection, GmailConnectionStatus, ScheduleFrequency

logger = logging.getLogger(__name__)

# Singleton scheduler instance
_scheduler: "GmailScheduler | None" = None


def get_scheduler() -> "GmailScheduler":
    """Get the global scheduler instance."""
    global _scheduler
    if _scheduler is None:
        _scheduler = GmailScheduler()
    return _scheduler


class GmailScheduler:
    """Manages scheduled Gmail scans using APScheduler."""

    JOB_PREFIX = "gmail_scan_"

    def __init__(self) -> None:
        self._scheduler = BackgroundScheduler(timezone="UTC")
        self._started = False

    @property
    def is_running(self) -> bool:
        return self._started

    def start(self, engine) -> None:
        """Start the scheduler and load existing schedules from DB."""
        if self._started:
            return

        self._engine = engine
        self._scheduler.start()
        self._started = True
        logger.info("Gmail scheduler started")

        self._load_existing_schedules()

    def shutdown(self) -> None:
        """Shut down the scheduler."""
        if self._started:
            self._scheduler.shutdown(wait=False)
            self._started = False
            logger.info("Gmail scheduler shut down")

    def _load_existing_schedules(self) -> None:
        """Load all active schedules from database on startup."""
        with Session(self._engine) as session:
            connections = session.exec(
                select(GmailConnection).where(
                    GmailConnection.status == GmailConnectionStatus.CONNECTED,
                    GmailConnection.schedule_frequency.isnot(None),
                )
            ).all()

            for conn in connections:
                try:
                    self._add_job(conn.ledger_id, conn.schedule_frequency, conn.schedule_hour)
                except Exception:
                    logger.exception("Failed to schedule job for ledger %s", conn.ledger_id)

        logger.info("Loaded %d existing scheduled scans", len(connections))

    def schedule_scan(
        self,
        ledger_id: uuid.UUID,
        frequency: ScheduleFrequency,
        hour: int,
        day_of_week: int | None = None,
    ) -> None:
        """Schedule or update a recurring scan for a ledger."""
        # Remove existing job if any
        self.cancel_scan(ledger_id)

        # Create cron trigger based on frequency
        self._add_job(ledger_id, frequency, hour, day_of_week)
        logger.info(
            "Scheduled %s scan for ledger %s at hour %d",
            frequency.value,
            ledger_id,
            hour,
        )

    def cancel_scan(self, ledger_id: uuid.UUID) -> None:
        """Cancel a scheduled scan for a ledger."""
        job_id = f"{self.JOB_PREFIX}{ledger_id}"
        try:
            self._scheduler.remove_job(job_id)
            logger.info("Cancelled scheduled scan for ledger %s", ledger_id)
        except Exception:
            pass  # Job may not exist

    def get_next_run_time(self, ledger_id: uuid.UUID) -> datetime | None:
        """Get the next scheduled run time for a ledger."""
        job_id = f"{self.JOB_PREFIX}{ledger_id}"
        job = self._scheduler.get_job(job_id)
        if job and job.next_run_time:
            return job.next_run_time.replace(tzinfo=UTC)
        return None

    def _add_job(
        self,
        ledger_id: uuid.UUID,
        frequency: ScheduleFrequency,
        hour: int | None,
        day_of_week: int | None = None,
    ) -> None:
        """Add a scan job to the scheduler."""
        job_id = f"{self.JOB_PREFIX}{ledger_id}"
        scan_hour = hour if hour is not None else 6  # Default to 6 AM

        if frequency == ScheduleFrequency.DAILY:
            trigger = CronTrigger(hour=scan_hour, minute=0)
        else:  # WEEKLY
            dow = day_of_week if day_of_week is not None else 0  # Default Monday
            trigger = CronTrigger(day_of_week=dow, hour=scan_hour, minute=0)

        self._scheduler.add_job(
            self._execute_scheduled_scan,
            trigger=trigger,
            id=job_id,
            args=[str(ledger_id)],
            replace_existing=True,
            misfire_grace_time=3600,  # Allow up to 1 hour late
        )

    def _execute_scheduled_scan(self, ledger_id_str: str) -> None:
        """Execute a scheduled scan job."""
        from src.models.gmail_scan import ScanTriggerType
        from src.services.gmail_import_service import GmailImportService

        ledger_id = uuid.UUID(ledger_id_str)

        try:
            with Session(self._engine) as session:
                # Look up ledger for user_id
                from src.models.ledger import Ledger

                ledger = session.exec(select(Ledger).where(Ledger.id == ledger_id)).first()
                if not ledger:
                    logger.error("Ledger %s not found for scheduled scan", ledger_id)
                    return

                import_service = GmailImportService(session)
                connection = import_service.get_connection(ledger_id)

                if not connection or connection.status != GmailConnectionStatus.CONNECTED:
                    logger.warning(
                        "No active Gmail connection for ledger %s, skipping scan", ledger_id
                    )
                    return

                job = import_service.execute_scan(
                    ledger_id=ledger_id,
                    user_id=ledger.user_id,
                    trigger_type=ScanTriggerType.SCHEDULED,
                )

                logger.info(
                    "Scheduled scan completed for ledger %s: %d statements found",
                    ledger_id,
                    job.statements_found,
                )
        except Exception:
            logger.exception("Scheduled scan failed for ledger %s", ledger_id)

    @staticmethod
    def calculate_next_scan(
        frequency: ScheduleFrequency | None,
        hour: int | None,
        day_of_week: int | None = None,
    ) -> datetime | None:
        """Calculate the next scan time without needing the scheduler running."""
        if not frequency or hour is None:
            return None

        now = datetime.now(UTC)
        scan_hour = hour

        if frequency == ScheduleFrequency.DAILY:
            next_run = now.replace(hour=scan_hour, minute=0, second=0, microsecond=0)
            if next_run <= now:
                next_run += timedelta(days=1)
            return next_run

        # WEEKLY
        dow = day_of_week if day_of_week is not None else 0
        next_run = now.replace(hour=scan_hour, minute=0, second=0, microsecond=0)
        days_ahead = dow - now.weekday()
        if days_ahead < 0 or (days_ahead == 0 and next_run <= now):
            days_ahead += 7
        next_run += timedelta(days=days_ahead)
        return next_run
