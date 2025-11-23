import sys
import os
from unittest.mock import Mock, patch
from parser.scheduler import (
    scheduled_update, start_scheduler, shutdown_scheduler,
    scheduler as global_scheduler
)
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logger = logging.getLogger(__name__)


class TestScheduler:
    """Тесты для планировщика"""

    def setup_method(self):
        """Сброс глобального планировщика перед каждым тестом"""
        global_scheduler = None

    def teardown_method(self):
        """Очистка после каждого теста"""
        if global_scheduler and global_scheduler.running:
            global_scheduler.shutdown()

    @patch('parser.scheduler.SessionLocal')
    @patch('parser.scheduler.update_problems')
    def test_scheduled_update_success(self, mock_update_problems, mock_session_local):
        """Тест успешного выполнения запланированного обновления"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_update_problems.return_value = True
        scheduled_update()
        mock_session_local.assert_called_once()
        mock_update_problems.assert_called_once_with(mock_db)
        mock_db.close.assert_called_once()

    @patch('parser.scheduler.SessionLocal')
    @patch('parser.scheduler.update_problems')
    def test_scheduled_update_failure(self, mock_update_problems, mock_session_local):
        """Тест неудачного выполнения запланированного обновления"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_update_problems.return_value = False
        scheduled_update()
        mock_update_problems.assert_called_once_with(mock_db)
        mock_db.close.assert_called_once()

    @patch('parser.scheduler.SessionLocal')
    @patch('parser.scheduler.update_problems')
    def test_scheduled_update_exception(self, mock_update_problems, mock_session_local):
        """Тест обработки исключения в запланированном обновлении"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_update_problems.side_effect = Exception("Database error")
        scheduled_update()
        mock_update_problems.assert_called_once_with(mock_db)
        mock_db.close.assert_called_once()

    @patch('parser.scheduler.SessionLocal')
    @patch('parser.scheduler.update_problems')
    def test_scheduled_update_db_closed_on_error(self, mock_update_problems, mock_session_local):
        """Тест что соединение с БД закрывается даже при ошибке"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_update_problems.side_effect = Exception("Some error")
        scheduled_update()
        mock_db.close.assert_called_once()

    @patch('parser.scheduler.scheduled_update')
    @patch('parser.scheduler.BackgroundScheduler')
    @patch('parser.scheduler.config')
    def test_start_scheduler_already_running(self, mock_config, mock_scheduler_class, mock_scheduled_update):
        """Тест запуска планировщика когда он уже работает"""
        mock_config.UPDATE_INTERVAL_HOURS = 6
        mock_scheduler = Mock()
        mock_scheduler.running = True
        mock_scheduler_class.return_value = mock_scheduler

        import parser.scheduler
        parser.scheduler.scheduler = mock_scheduler
        start_scheduler()
        mock_scheduler_class.assert_not_called()
        mock_scheduled_update.assert_called_once()
        mock_scheduler.add_job.assert_called_once()

    @patch('parser.scheduler.scheduled_update')
    @patch('parser.scheduler.BackgroundScheduler')
    @patch('parser.scheduler.config')
    def test_start_scheduler_initial_update_called(self, mock_config, mock_scheduler_class, mock_scheduled_update):
        """Тест что начальное обновление вызывается при запуске"""
        mock_config.UPDATE_INTERVAL_HOURS = 6
        mock_scheduler = Mock()
        mock_scheduler.running = False
        mock_scheduler_class.return_value = mock_scheduler
        start_scheduler()
        mock_scheduled_update.assert_called_once()

    def test_shutdown_scheduler_when_running(self):
        """Тест остановки работающего планировщика"""
        mock_scheduler = Mock()
        mock_scheduler.running = True

        import parser.scheduler
        parser.scheduler.scheduler = mock_scheduler

        shutdown_scheduler()
        mock_scheduler.shutdown.assert_called_once()

    def test_shutdown_scheduler_when_not_running(self):
        """Тест остановки неработающего планировщика"""
        mock_scheduler = Mock()
        mock_scheduler.running = False

        import parser.scheduler
        parser.scheduler.scheduler = mock_scheduler
        shutdown_scheduler()

        mock_scheduler.shutdown.assert_not_called()

    def test_shutdown_scheduler_when_none(self):
        """Тест остановки когда планировщик не инициализирован"""
        import parser.scheduler
        parser.scheduler.scheduler = None
        shutdown_scheduler()

    @patch('parser.scheduler.logger')
    def test_shutdown_scheduler_logging(self, mock_logger):
        """Тест логирования при остановке планировщика"""
        mock_scheduler = Mock()
        mock_scheduler.running = True
        import parser.scheduler
        parser.scheduler.scheduler = mock_scheduler
        shutdown_scheduler()
        mock_logger.info.assert_called_once_with("🛑 Process: Scheduler stopped")

    @patch('parser.scheduler.SessionLocal')
    @patch('parser.codeforces_parser.CodeforcesParser')
    def test_scheduled_update_integration(self, mock_parser_class, mock_session_local):
        """Интеграционный тест scheduled_update с CodeforcesParser"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_parser = Mock()
        mock_parser.parse_and_save_problems.return_value = True
        mock_parser_class.return_value = mock_parser
        with patch('parser.scheduler.update_problems') as mock_update_problems:
            mock_update_problems.return_value = True
            scheduled_update()
            mock_update_problems.assert_called_once_with(mock_db)
            mock_db.close.assert_called_once()

    @patch('parser.scheduler.logger')
    @patch('parser.scheduler.SessionLocal')
    @patch('parser.scheduler.update_problems')
    def test_scheduled_update_logging(self, mock_update_problems, mock_session_local, mock_logger):
        """Тест логирования в scheduled_update"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_update_problems.return_value = True
        scheduled_update()
        mock_logger.info.assert_any_call("🔄 Process: Starting scheduled problems update...")
        mock_logger.info.assert_any_call("✅ Process: Scheduled update completed successfully")

    @patch('parser.scheduler.logger')
    @patch('parser.scheduler.SessionLocal')
    @patch('parser.scheduler.update_problems')
    def test_scheduled_update_error_logging(self, mock_update_problems, mock_session_local, mock_logger):
        """Тест логирования ошибок в scheduled_update"""
        mock_db = Mock()
        mock_session_local.return_value = mock_db
        mock_update_problems.return_value = False
        scheduled_update()
        mock_logger.error.assert_called_once_with("❌ Process: Scheduled update failed")
