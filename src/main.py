import logging
import threading
import time
from database.database import init_db
from bot.telegram_bot import run_bot

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


def run_parser_daemon():
    """Запуск парсера в фоновом режиме с периодическим обновлением"""
    import sys
    import os
    sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

    from database.database import SessionLocal
    from parser.codeforces_parser import CodeforcesParser

    logger.info("🔄 Parser daemon started")

    while True:
        try:
            logger.info("🔄 Running scheduled parser update...")
            db = SessionLocal()
            parser = CodeforcesParser()
            if parser.parse_and_save_problems(db):
                logger.info("✅ Parser update completed successfully")
            else:
                logger.error("❌ Parser update failed")
            db.close()
        except Exception as e:
            logger.error(f"❌ Parser error: {e}")
        logger.info("⏰ Parser sleeping for 1 hour...")
        time.sleep(3600)


def main():
    """Основная функция запуска"""
    logger.info("🚀 Starting Codeforces Parser Bot with integrated scheduler...")
    logger.info("🗄️ Initializing database...")
    init_db()
    logger.info("✅ Database initialized")
    logger.info("🔄 Starting parser daemon in background thread...")
    parser_thread = threading.Thread(target=run_parser_daemon, daemon=True)
    parser_thread.start()
    logger.info("✅ Parser daemon started")
    logger.info("🤖 Starting Telegram bot...")
    run_bot()


if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        logger.info("🛑 Application stopped by user")
    except Exception as e:
        logger.error(f"❌ Application error: {e}")
