from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from sqlalchemy.exc import OperationalError
import logging
import urllib.parse
from config.config import config

logger = logging.getLogger(__name__)


def create_safe_database_url():
    """Создает безопасный DATABASE_URL с правильной кодировкой"""
    try:
        if hasattr(config, 'DATABASE_URL') and config.DATABASE_URL:
            return config.DATABASE_URL

        db_config = {
            'host': getattr(config, 'DATABASE_HOST', 'localhost'),
            'port': getattr(config, 'DATABASE_PORT', '5432'),
            'database': getattr(config, 'DATABASE_NAME', 'codeforces_db'),
            'username': getattr(config, 'DATABASE_USER', 'codeforces_user'),
            'password': getattr(config, 'DATABASE_PASSWORD', 'password')
        }

        password = urllib.parse.quote_plus(db_config['password'])

        return f"postgresql://{db_config['username']}:" \
               f"{password}@{db_config['host']}:{db_config['port']}/{db_config['database']}"

    except Exception as e:
        logger.error(f"Error creating database URL: {e}")
        return "postgresql://codeforces_user:password@localhost:5432/codeforces_db"


database_url = create_safe_database_url()
logger.info(f"Database URL: {database_url.replace('password', '***')}")

try:
    engine = create_engine(
        database_url,
        echo=False,
        pool_pre_ping=True,
        connect_args={
            'options': '-c client_encoding=utf8'
        }
    )
except Exception as e:
    logger.error(f"Error creating database engine: {e}")
    raise

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def get_db():
    """Генератор сессий базы данных"""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def init_db():
    """Инициализация базы данных (создание таблиц)"""
    from .models import Base

    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        logger.info("Database connection successful")

        Base.metadata.create_all(bind=engine)
        logger.info("Database tables created successfully")

    except OperationalError as e:
        logger.error(f"Database connection failed: {e}")
        raise
    except Exception as e:
        logger.error(f"Error creating database tables: {e}")
        raise


def test_connection():
    """Тест подключения к базе данных"""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            logger.info(f"PostgreSQL version: {version}")
            return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False
