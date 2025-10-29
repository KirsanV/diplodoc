import pytest
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
from bot.telegram_bot import TelegramBot, CHOOSING_RATING, CHOOSING_TOPIC

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestTelegramBotSync:
    """Синхронные тесты для Telegram бота."""

    @pytest.fixture
    def telegram_bot(self):
        """Фикстура для создания экземпляра бота."""
        return TelegramBot("test_token")

    @pytest.fixture
    def mock_problem(self):
        """Фикстура для создания mock проблемы."""
        problem = Mock()
        problem.full_code = "123A"
        problem.name = "Test Problem"
        problem.rating = 800
        problem.solved_count = 1500
        problem.codeforces_url = "https://codeforces.com/problemset/problem/123/A"

        topic1 = Mock()
        topic1.name = "math"
        topic2 = Mock()
        topic2.name = "brute force"
        problem.topics = [topic1, topic2]

        return problem

    def test_bot_initialization(self, telegram_bot):
        """Тест инициализации бота."""
        assert telegram_bot.token == "test_token"
        assert telegram_bot.application is not None

    def test_handlers_setup(self, telegram_bot):
        """Тест настройки обработчиков."""
        handlers = telegram_bot.application.handlers
        assert len(handlers) > 0

        command_handlers = [h for h in handlers[0] if hasattr(h, 'commands')]
        assert len(command_handlers) > 0

    def test_format_problem_details(self, telegram_bot, mock_problem):
        """Тест форматирования деталей задачи."""
        formatted = telegram_bot._format_problem_details(mock_problem)

        assert "Задача 123A" in formatted
        assert "Test Problem" in formatted
        assert "800" in formatted
        assert "1500" in formatted
        assert "math, brute force" in formatted
        assert "codeforces.com" in formatted

    def test_format_problem_details_no_rating(self, telegram_bot):
        """Тест форматирования задачи без рейтинга."""
        problem = Mock()
        problem.full_code = "123A"
        problem.name = "Test Problem"
        problem.rating = None
        problem.solved_count = 1500
        problem.codeforces_url = "https://codeforces.com/problemset/problem/123/A"
        problem.topics = []

        formatted = telegram_bot._format_problem_details(problem)

        assert "N/A" in formatted
        assert "1500" in formatted

    def test_format_problem_details_no_topics(self, telegram_bot):
        """Тест форматирования задачи без тем."""
        problem = Mock()
        problem.full_code = "123A"
        problem.name = "Test Problem"
        problem.rating = 800
        problem.solved_count = 1500
        problem.codeforces_url = "https://codeforces.com/problemset/problem/123/A"
        problem.topics = []

        formatted = telegram_bot._format_problem_details(problem)

        assert "Темы:" not in formatted

    def test_bot_methods_exist(self, telegram_bot):
        """Тест что все методы бота существуют."""
        assert hasattr(telegram_bot, 'start')
        assert hasattr(telegram_bot, 'help')
        assert hasattr(telegram_bot, 'search')
        assert hasattr(telegram_bot, 'start_problem_selection')
        assert hasattr(telegram_bot, 'select_rating')
        assert hasattr(telegram_bot, 'select_topic')
        assert hasattr(telegram_bot, 'handle_text')
        assert hasattr(telegram_bot, 'cancel')
        assert hasattr(telegram_bot, '_format_problem_details')

    @patch('bot.telegram_bot.SessionLocal')
    @patch('bot.telegram_bot.TaskService.get_available_ratings')
    def test_start_problem_selection_no_ratings(self, mock_ratings, mock_session, telegram_bot):
        """Тест начала подбора задач когда нет рейтингов."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_ratings.return_value = []

        mock_update = AsyncMock()
        mock_update.message = AsyncMock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_data = {}

        import asyncio
        result = asyncio.run(telegram_bot.start_problem_selection(mock_update, mock_context))

        mock_update.message.reply_text.assert_called_once()
        assert "нет задач" in mock_update.message.reply_text.call_args[0][0]
        assert result == -1

    @patch('bot.telegram_bot.SessionLocal')
    @patch('bot.telegram_bot.TaskService.get_available_ratings')
    def test_start_problem_selection_with_ratings(self, mock_ratings, mock_session, telegram_bot):
        """Тест начала подбора задач с доступными рейтингами."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_ratings.return_value = [800, 900, 1000]

        mock_update = AsyncMock()
        mock_update.message = AsyncMock()
        mock_update.message.reply_text = AsyncMock()
        mock_context = AsyncMock()
        mock_context.user_data = {}

        import asyncio
        result = asyncio.run(telegram_bot.start_problem_selection(mock_update, mock_context))

        mock_update.message.reply_text.assert_called_once()
        call_args = mock_update.message.reply_text.call_args
        assert "Выберите сложность" in call_args[0][0]
        assert call_args[1]['reply_markup'] is not None


class TestRunBotSync:
    """Синхронные тесты для функции запуска бота."""

    @patch('bot.telegram_bot.config')
    @patch('bot.telegram_bot.TelegramBot')
    def test_run_bot_success(self, mock_telegram_bot, mock_config):
        """Тест успешного запуска бота."""
        from bot.telegram_bot import run_bot

        mock_config.TELEGRAM_BOT_TOKEN = "valid_token"
        mock_bot_instance = Mock()
        mock_telegram_bot.return_value = mock_bot_instance

        run_bot()

        mock_telegram_bot.assert_called_once_with("valid_token")
        mock_bot_instance.application.run_polling.assert_called_once()

    @patch('bot.telegram_bot.config')
    @patch('bot.telegram_bot.logger')
    def test_run_bot_no_token(self, mock_logger, mock_config):
        """Тест запуска бота без токена."""
        from bot.telegram_bot import run_bot

        mock_config.TELEGRAM_BOT_TOKEN = None

        run_bot()

        mock_logger.error.assert_called()
        error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
        assert any("TELEGRAM_BOT_TOKEN not found" in str(call) for call in error_calls)


class TestBotIntegration:
    """Интеграционные тесты для бота."""

    def test_bot_creation_integration(self):
        """Интеграционный тест создания бота."""
        bot = TelegramBot("test_token")

        assert bot.token == "test_token"
        assert bot.application is not None
        assert hasattr(bot, 'setup_handlers')

        bot.setup_handlers()
        assert len(bot.application.handlers) > 0

    def test_problem_formatting_integration(self):
        """Интеграционный тест форматирования проблемы."""
        bot = TelegramBot("test_token")

        class MockTopic:
            """Mock класса темы."""
            def __init__(self, name):
                self.name = name

            def __repr__(self):
                return f"Topic({self.name})"

        class MockProblem:
            """Mock класса проблемы."""
            def __init__(self):
                self.contest_id = 123
                self.problem_index = "A"
                self.name = "Test Problem"
                self.rating = 800
                self.solved_count = 1500
                self.topics = [MockTopic("math"), MockTopic("graphs")]

            @property
            def full_code(self):
                return f"{self.contest_id}{self.problem_index}"

            @property
            def codeforces_url(self):
                return f"https://codeforces.com/problemset/problem/{self.contest_id}/{self.problem_index}"

        problem = MockProblem()
        formatted = bot._format_problem_details(problem)

        assert "123A" in formatted
        assert "Test Problem" in formatted
        assert "800" in formatted
        assert "1500" in formatted
        assert "math" in formatted
        assert "graphs" in formatted
        assert "codeforces.com" in formatted

        lines = formatted.split('\n')
        assert any("Задача 123A" in line for line in lines)
        assert any("Название:" in line for line in lines)
        assert any("Сложность:" in line for line in lines)
        assert any("Количество решений:" in line for line in lines)
        assert any("Темы:" in line for line in lines)


class TestTelegramBotAsync:
    """Асинхронные тесты для Telegram бота."""

    @pytest.fixture
    def telegram_bot(self):
        """Фикстура для создания экземпляра бота."""
        return TelegramBot("test_token")

    @pytest.fixture
    def mock_update(self):
        """Фикстура для создания mock update."""
        update = AsyncMock()
        update.message = AsyncMock()
        update.message.reply_text = AsyncMock()
        update.message.text = "test"
        update.effective_user = Mock()
        update.effective_user.first_name = "TestUser"
        return update

    @pytest.fixture
    def mock_context(self):
        """Фикстура для создания mock context."""
        context = AsyncMock()
        context.user_data = {}
        context.args = []
        return context

    @pytest.mark.asyncio
    async def test_start_command(self, telegram_bot, mock_update, mock_context):
        """Тест команды /start."""
        await telegram_bot.start(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Привет" in response_text
        assert "TestUser" in response_text
        assert "/search" in response_text
        assert "/problems" in response_text

    @pytest.mark.asyncio
    async def test_help_command(self, telegram_bot, mock_update, mock_context):
        """Тест команды /help."""
        await telegram_bot.help(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Справка" in response_text
        assert "/search" in response_text
        assert "/problems" in response_text

    @pytest.mark.asyncio
    async def test_search_command_no_args(self, telegram_bot, mock_update, mock_context):
        """Тест команды /search без аргументов."""
        await telegram_bot.search(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Использование" in response_text
        assert "/search" in response_text

    @pytest.mark.asyncio
    @patch('bot.telegram_bot.SessionLocal')
    @patch('bot.telegram_bot.TaskService.search_problems')
    async def test_search_command_multiple_results(self, mock_search, mock_session, telegram_bot, mock_update,
                                                   mock_context):
        """Тест команды /search с несколькими результатами."""
        mock_db = Mock()
        mock_session.return_value = mock_db

        problems = []
        for i in range(3):
            problem = Mock()
            problem.full_code = f"12{i}A"
            problem.name = f"Problem {i}"
            problem.rating = 1500 + i
            problem.solved_count = 1000 + i
            problem.codeforces_url = f"http://test.com/{i}"
            problems.append(problem)

        mock_search.return_value = problems
        mock_context.args = ["problem"]

        await telegram_bot.search(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Найдено задач: 3" in response_text
        assert "120A" in response_text
        assert "121A" in response_text
        assert "122A" in response_text

    @pytest.mark.asyncio
    @patch('bot.telegram_bot.SessionLocal')
    @patch('bot.telegram_bot.TaskService.search_problems')
    async def test_search_command_no_results(self, mock_search, mock_session, telegram_bot, mock_update, mock_context):
        """Тест команды /search без результатов."""
        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_search.return_value = []
        mock_context.args = ["nonexistent"]

        await telegram_bot.search(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "не найдены" in response_text
        assert "nonexistent" in response_text

    @pytest.mark.asyncio
    async def test_select_rating_valid(self, telegram_bot, mock_update, mock_context):
        """Тест выбора валидного рейтинга."""
        mock_update.message.text = "⭐ 1500"
        mock_context.user_data = {}

        with patch('bot.telegram_bot.SessionLocal') as mock_session, \
                patch('bot.telegram_bot.TaskService.get_available_topics') as mock_topics:
            mock_db = Mock()
            mock_session.return_value = mock_db
            mock_topics.return_value = ["dp", "math", "greedy"]

            result = await telegram_bot.select_rating(mock_update, mock_context)

            assert result == CHOOSING_TOPIC
            assert mock_context.user_data['rating'] == 1500
            mock_update.message.reply_text.assert_called_once()
            response_text = mock_update.message.reply_text.call_args[0][0]
            assert "Выбрана сложность: 1500" in response_text

    @pytest.mark.asyncio
    async def test_select_rating_invalid(self, telegram_bot, mock_update, mock_context):
        """Тест выбора невалидного рейтинга."""
        mock_update.message.text = "invalid rating"
        mock_context.user_data = {}

        result = await telegram_bot.select_rating(mock_update, mock_context)

        assert result == CHOOSING_RATING
        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Пожалуйста, выберите сложность из предложенных вариантов" in response_text

    @pytest.mark.asyncio
    @patch('bot.telegram_bot.SessionLocal')
    @patch('bot.telegram_bot.TaskService.get_problems_by_filters')
    async def test_select_topic_with_results(self, mock_get_problems, mock_session, telegram_bot, mock_update,
                                             mock_context):
        """Тест выбора темы с результатами."""
        mock_update.message.text = "📚 dp"
        mock_context.user_data = {'rating': 1500}

        mock_db = Mock()
        mock_session.return_value = mock_db

        mock_problem = Mock()
        mock_problem.full_code = "123A"
        mock_problem.name = "Test Problem"
        mock_problem.solved_count = 1000
        mock_problem.codeforces_url = "http://test.com"
        mock_get_problems.return_value = [mock_problem]

        result = await telegram_bot.select_topic(mock_update, mock_context)

        assert result == -1
        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Подборка задач" in response_text
        assert "123A" in response_text

    @pytest.mark.asyncio
    @patch('bot.telegram_bot.SessionLocal')
    @patch('bot.telegram_bot.TaskService.get_problems_by_filters')
    async def test_select_topic_no_results(self, mock_get_problems, mock_session, telegram_bot, mock_update,
                                           mock_context):
        """Тест выбора темы без результатов."""
        mock_update.message.text = "📚 nonexistent"
        mock_context.user_data = {'rating': 1500}

        mock_db = Mock()
        mock_session.return_value = mock_db
        mock_get_problems.return_value = []

        result = await telegram_bot.select_topic(mock_update, mock_context)

        assert result == -1
        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Не найдено задач" in response_text

    @pytest.mark.asyncio
    async def test_handle_text_unknown(self, telegram_bot, mock_update, mock_context):
        """Тест обработки неизвестного текста."""
        mock_update.message.text = "random text"

        await telegram_bot.handle_text(mock_update, mock_context)

        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Не понял ваш запрос" in response_text

    @pytest.mark.asyncio
    async def test_cancel_command(self, telegram_bot, mock_update, mock_context):
        """Тест команды отмены."""
        result = await telegram_bot.cancel(mock_update, mock_context)

        assert result == -1
        mock_update.message.reply_text.assert_called_once()
        response_text = mock_update.message.reply_text.call_args[0][0]
        assert "Операция отменена" in response_text
