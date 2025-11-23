import pytest
import sys
import os
from unittest.mock import Mock, patch
from database.database import (
    create_safe_database_url, get_db, init_db, test_connection,
    SessionLocal, engine
)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestDatabaseURL:
    """Тесты для создания URL базы данных"""

    @patch('database.database.config')
    def test_create_safe_database_url_from_config(self, mock_config):
        """Тест создания URL из конфигурации"""
        mock_config.DATABASE_URL = "postgresql://user:pass@host:5432/db"

        url = create_safe_database_url()

        assert url == "postgresql://user:pass@host:5432/db"

    @patch('database.database.config')
    def test_create_safe_database_url_from_components(self, mock_config):
        """Тест создания URL из компонентов"""
        mock_config.DATABASE_URL = None
        mock_config.DATABASE_HOST = "test_host"
        mock_config.DATABASE_PORT = "5433"
        mock_config.DATABASE_NAME = "test_db"
        mock_config.DATABASE_USER = "test_user"
        mock_config.DATABASE_PASSWORD = "test@pass#word"

        url = create_safe_database_url()

        assert "test%40pass%23word" in url
        assert url == "postgresql://test_user:test%40pass%23word@test_host:5433/test_db"

    @patch('database.database.config')
    def test_create_safe_database_url_default_values(self, mock_config):
        """Тест создания URL с значениями по умолчанию"""
        mock_config.DATABASE_URL = None
        if hasattr(mock_config, 'DATABASE_HOST'):
            delattr(mock_config, 'DATABASE_HOST')
        if hasattr(mock_config, 'DATABASE_PORT'):
            delattr(mock_config, 'DATABASE_PORT')
        if hasattr(mock_config, 'DATABASE_NAME'):
            delattr(mock_config, 'DATABASE_NAME')
        if hasattr(mock_config, 'DATABASE_USER'):
            delattr(mock_config, 'DATABASE_USER')
        if hasattr(mock_config, 'DATABASE_PASSWORD'):
            delattr(mock_config, 'DATABASE_PASSWORD')

        url = create_safe_database_url()

        expected_default = "postgresql://codeforces_user:password@localhost:5432/codeforces_db"
        assert url == expected_default

    @patch('database.database.config')
    @patch('database.database.logger')
    def test_create_safe_database_url_exception_handling(self, mock_logger, mock_config):
        """Тест обработки исключений при создании URL"""
        mock_config.DATABASE_URL = None
        mock_config.DATABASE_HOST = Mock(side_effect=Exception("Test error"))

        url = create_safe_database_url()

        expected_default = "postgresql://codeforces_user:password@localhost:5432/codeforces_db"
        assert url == expected_default
        mock_logger.error.assert_called()


class TestDatabaseConnection:
    """Тесты подключения к базе данных"""

    @patch('database.database.SessionLocal')
    def test_get_db_generator(self, mock_session_local):
        """Тест генератора сессий БД"""
        mock_session = Mock()
        mock_session_local.return_value = mock_session

        db_gen = get_db()
        db = next(db_gen)

        assert db == mock_session

        try:
            next(db_gen)
        except StopIteration:
            pass

        mock_session.close.assert_called_once()

    @patch('database.database.engine')
    @patch('database.database.logger')
    def test_init_db_connection_failed(self, mock_logger, mock_engine):
        """Тест неудачного подключения при инициализации БД"""
        from sqlalchemy.exc import OperationalError

        mock_engine.connect.side_effect = OperationalError("Connection failed", None, None)

        with pytest.raises(OperationalError):
            init_db()

        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("Database connection failed" in str(call) for call in error_calls)

    @patch('database.database.engine')
    @patch('database.database.logger')
    def test_test_connection_success(self, mock_logger, mock_engine):
        """Тест успешной проверки подключения"""
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = "PostgreSQL 13.0"

        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        result = test_connection()

        assert result is True
        mock_logger.info.assert_called_with("PostgreSQL version: PostgreSQL 13.0")

    @patch('database.database.engine')
    @patch('database.database.logger')
    def test_test_connection_failed(self, mock_logger, mock_engine):
        """Тест неудачной проверки подключения"""
        mock_engine.connect.side_effect = Exception("Connection test failed")

        result = test_connection()

        assert result is False
        mock_logger.error.assert_called_with("Database connection test failed: Connection test failed")


class TestDatabaseEngine:
    """Тесты для engine базы данных"""

    def test_engine_creation(self):
        """Тест что engine был создан"""
        assert engine is not None
        assert hasattr(engine, 'connect')
        assert hasattr(engine, 'dispose')

    def test_session_local_creation(self):
        """Тест что SessionLocal был создан"""
        assert SessionLocal is not None
        assert hasattr(SessionLocal, '__call__')


class TestDatabaseSimple:
    """Упрощенные тесты для базы данных"""

    def test_create_safe_database_url_simple(self):
        """Простой тест создания URL"""
        url = create_safe_database_url()
        assert isinstance(url, str)
        assert url.startswith('postgresql://')

    def test_get_db_returns_generator(self):
        """Тест что get_db возвращает генератор"""
        with patch('database.database.SessionLocal') as mock_session_local:
            mock_session = Mock()
            mock_session_local.return_value = mock_session

            db_gen = get_db()

            assert hasattr(db_gen, '__iter__')
            assert hasattr(db_gen, '__next__')

            db = next(db_gen)
            assert db == mock_session

            try:
                next(db_gen)
            except StopIteration:
                pass

    @patch('database.database.engine')
    def test_test_connection_returns_bool(self, mock_engine):
        """Тест что test_connection возвращает bool"""
        mock_conn = Mock()
        mock_result = Mock()
        mock_result.scalar.return_value = "test"

        mock_engine.connect.return_value.__enter__.return_value = mock_conn
        mock_conn.execute.return_value = mock_result

        result = test_connection()
        assert isinstance(result, bool)


@patch('database.database.config')
@patch('database.database.urllib.parse.quote_plus')
def test_password_encoding(mock_quote_plus, mock_config):
    """Тест кодирования пароля"""
    mock_config.DATABASE_URL = None
    mock_config.DATABASE_PASSWORD = "test@pass#word"
    mock_quote_plus.return_value = "encoded_password"

    create_safe_database_url()

    mock_quote_plus.assert_called_with("test@pass#word")
