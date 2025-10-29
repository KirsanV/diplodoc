import sys
import os
import logging
import time
from database.database import init_db, SessionLocal
from parser.codeforces_parser import CodeforcesParser

sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_parser_once():
    """Запуск парсера один раз"""
    logger.info("🔄 Running parser update...")
    db = SessionLocal()
    try:
        parser = CodeforcesParser()
        if parser.parse_and_save_problems(db):
            logger.info("✅ Parser update completed successfully")
        else:
            logger.error("❌ Parser update failed")
    except Exception as e:
        logger.error(f"❌ Parser error: {e}")
    finally:
        db.close()


def run_parser_periodically():
    """Запуск парсера периодически"""
    logger.info("🚀 Starting periodic parser...")

    init_db()
    logger.info("✅ Database initialized")

    while True:
        run_parser_once()
        logger.info("⏰ Waiting 1 hour until next update...")
        time.sleep(3600)


if __name__ == "__main__":
    try:
        if len(sys.argv) > 1 and sys.argv[1] == "daemon":
            run_parser_periodically()
        else:
            run_parser_once()

    except KeyboardInterrupt:
        logger.info("🛑 Parser stopped by user")
