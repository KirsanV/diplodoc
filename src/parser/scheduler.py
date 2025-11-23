import logging
from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.database import SessionLocal
from .codeforces_parser import update_problems
from config.config import config

logger = logging.getLogger(__name__)
scheduler = None


def scheduled_update():
    """Запланированное обновление задач"""
    logger.info("🔄 Process: Starting scheduled problems update...")
    db = SessionLocal()
    try:
        success = update_problems(db)
        if success:
            logger.info("✅ Process: Scheduled update completed successfully")
        else:
            logger.error("❌ Process: Scheduled update failed")
    except Exception as e:
        logger.error(f"❌ Process: Error in scheduled update: {e}")
    finally:
        db.close()


def start_scheduler():
    """Запуск планировщика"""
    global scheduler

    try:
        if scheduler is None:
            scheduler = BackgroundScheduler()

        logger.info("🔄 Process: Running initial problems update...")
        scheduled_update()

        trigger = IntervalTrigger(hours=config.UPDATE_INTERVAL_HOURS)
        scheduler.add_job(
            scheduled_update,
            trigger=trigger,
            id='update_problems',
            name='Update Codeforces problems',
            replace_existing=True
        )

        if not scheduler.running:
            scheduler.start()
            logger.info(f"✅ Process: Scheduler started with {config.UPDATE_INTERVAL_HOURS} hour interval")
        else:
            logger.info("✅ Process: Scheduler already running")

    except Exception as e:
        logger.error(f"❌ Process: Failed to start scheduler: {e}")


def shutdown_scheduler():
    """Остановка планировщика"""
    global scheduler
    if scheduler is not None and hasattr(scheduler, 'running') and scheduler.running:
        scheduler.shutdown()
        scheduler = None
        logger.info("🛑 Process: Scheduler stopped")
