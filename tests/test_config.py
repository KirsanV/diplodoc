import os
import sys
from unittest.mock import patch
import importlib


sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestConfig:
    """Тесты для конфигурации приложения"""

    def reload_config_module(self):
        """Перезагружает модуль config"""
        if 'config.config' in sys.modules:
            del sys.modules['config.config']
        import config.config
        importlib.reload(config.config)
        return config.config

    @patch.dict(os.environ, {'TELEGRAM_BOT_TOKEN': ''}, clear=True)
    def test_config_telegram_token_empty_string(self):
        """Тест что TELEGRAM_BOT_TOKEN пустая строка если установлена пустая"""
        config_module = self.reload_config_module()
        test_config = config_module.Config()
        assert test_config.TELEGRAM_BOT_TOKEN == ''

    def test_config_singleton_pattern(self):
        """Тест что config является синглтоном"""
        config_module = self.reload_config_module()
        config1 = config_module.config
        config2 = config_module.config
        assert config1 is config2

    @patch.dict(os.environ, {}, clear=True)
    def test_config_immutable_constants(self):
        """Тест что константы не меняются"""
        config_module = self.reload_config_module()
        test_config = config_module.Config()

        assert test_config.CODEFORCES_URL == "https://codeforces.com/api/problemset.problems"
        assert test_config.UPDATE_INTERVAL_HOURS == 1


class TestConfigEdgeCases:
    """Тесты граничных случаев для конфигурации"""

    def reload_config_module(self):
        """Перезагружает модуль config"""
        if 'config.config' in sys.modules:
            del sys.modules['config.config']
        import config.config
        importlib.reload(config.config)
        return config.config

    @patch.dict(os.environ, {}, clear=True)
    def test_config_type_validation(self):
        """Тест типов данных конфигурации"""
        config_module = self.reload_config_module()
        test_config = config_module.Config()

        assert isinstance(test_config.DATABASE_URL, str)
        assert test_config.TELEGRAM_BOT_TOKEN is None or isinstance(test_config.TELEGRAM_BOT_TOKEN, str)
        assert isinstance(test_config.CODEFORCES_URL, str)
        assert isinstance(test_config.UPDATE_INTERVAL_HOURS, int)
        assert isinstance(test_config.DATABASE_HOST, str)
        assert isinstance(test_config.DATABASE_PORT, str)
        assert isinstance(test_config.DATABASE_NAME, str)
        assert isinstance(test_config.DATABASE_USER, str)
        assert isinstance(test_config.DATABASE_PASSWORD, str)


@patch.dict(os.environ, {}, clear=True)
def test_config_module_import():
    """Тест что модуль конфигурации может быть импортирован"""
    if 'config.config' in sys.modules:
        del sys.modules['config.config']
    import config.config
    importlib.reload(config.config)

    assert config.config.Config is not None
    assert config.config.config is not None


class TestConfigRealValues:
    """Тесты с реальными значениями (отдельно от моков)"""

    def test_config_attributes_exist(self):
        """Тест что все обязательные атрибуты конфигурации существуют"""
        from config.config import config

        assert hasattr(config, 'DATABASE_URL')
        assert hasattr(config, 'TELEGRAM_BOT_TOKEN')
        assert hasattr(config, 'CODEFORCES_URL')
        assert hasattr(config, 'UPDATE_INTERVAL_HOURS')
        assert hasattr(config, 'DATABASE_HOST')
        assert hasattr(config, 'DATABASE_PORT')
        assert hasattr(config, 'DATABASE_NAME')
        assert hasattr(config, 'DATABASE_USER')
        assert hasattr(config, 'DATABASE_PASSWORD')

    def test_config_constants_are_correct(self):
        """Тест что константы имеют правильные значения"""
        from config.config import config

        assert config.CODEFORCES_URL == "https://codeforces.com/api/problemset.problems"
        assert config.UPDATE_INTERVAL_HOURS == 1
