"""
Adaptive scheduler — runs scraping at the right frequency based on time of year.
Earnings season: every 30 mins. Off-season: once daily.
"""
import logging
from datetime import datetime
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from config import (
    EARNINGS_SEASON_MONTHS,
    SCHEDULER_INTERVAL_EARNINGS_SEASON,
    SCHEDULER_INTERVAL_OFF_SEASON,
)
from scraper.orchestrator import run_all_companies

logger = logging.getLogger(__name__)

_scheduler = BackgroundScheduler()
_current_interval = None


def is_earnings_season() -> bool:
    return datetime.now().month in EARNINGS_SEASON_MONTHS


def _scraper_job():
    """The job that runs on schedule."""
    logger.info(f"⏰ Scheduler tick at {datetime.now().isoformat()}")
    try:
        run_all_companies(days_back=2)
    except Exception as e:
        logger.error(f"Scheduler job failed: {e}")


def _get_interval_minutes() -> int:
    return SCHEDULER_INTERVAL_EARNINGS_SEASON if is_earnings_season() else SCHEDULER_INTERVAL_OFF_SEASON


def start_scheduler():
    global _current_interval
    interval = _get_interval_minutes()
    _current_interval = interval

    _scheduler.add_job(
        _scraper_job,
        trigger=IntervalTrigger(minutes=interval),
        id="scraper_job",
        replace_existing=True,
        max_instances=1,    # Never run two overlapping instances
    )
    _scheduler.add_job(
        _check_and_adapt_schedule,
        trigger=IntervalTrigger(hours=6),  # Check every 6h if season changed
        id="adapt_job",
        replace_existing=True,
    )
    _scheduler.start()
    season = "earnings season" if is_earnings_season() else "off-season"
    logger.info(f"✅ Scheduler started — {season} mode, running every {interval} minutes.")


def _check_and_adapt_schedule():
    """Dynamically adjust interval if we entered/left earnings season."""
    global _current_interval
    new_interval = _get_interval_minutes()
    if new_interval != _current_interval:
        logger.info(f"Season changed! Adjusting scheduler to {new_interval} min intervals.")
        _scheduler.reschedule_job(
            "scraper_job",
            trigger=IntervalTrigger(minutes=new_interval),
        )
        _current_interval = new_interval


def stop_scheduler():
    _scheduler.shutdown(wait=False)
    logger.info("Scheduler stopped.")
