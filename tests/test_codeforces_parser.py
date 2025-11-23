import pytest
import sys
import os
from unittest.mock import Mock, patch
from sqlalchemy.orm import Session
from parser.codeforces_parser import CodeforcesParser, update_problems
from database.models import Problem, Topic
from config.config import config
import logging
import requests

logger = logging.getLogger(__name__)

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestCodeforcesParser:
    """Тесты для CodeforcesParser"""

    @pytest.fixture
    def parser(self):
        return CodeforcesParser()

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def sample_problems_data(self):
        return {
            'status': 'OK',
            'result': {
                'problems': [
                    {
                        'contestId': 1,
                        'index': 'A',
                        'name': 'Test Problem A',
                        'rating': 1500,
                        'tags': ['dp', 'math']
                    },
                    {
                        'contestId': 1,
                        'index': 'B',
                        'name': 'Test Problem B',
                        'rating': 1600,
                        'tags': ['greedy', 'graphs']
                    }
                ],
                'problemStatistics': [
                    {
                        'contestId': 1,
                        'index': 'A',
                        'solvedCount': 1000
                    },
                    {
                        'contestId': 1,
                        'index': 'B',
                        'solvedCount': 500
                    }
                ]
            }
        }

    @pytest.fixture
    def sample_api_error_data(self):
        return {
            'status': 'FAILED',
            'comment': 'Internal error'
        }

    @patch('parser.codeforces_parser.requests.Session.get')
    def test_fetch_problems_success(self, mock_get, parser, sample_problems_data):
        """Тест успешного получения задач"""
        mock_response = Mock()
        mock_response.json.return_value = sample_problems_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = parser.fetch_problems()

        assert result is not None
        assert 'problems' in result
        assert len(result['problems']) == 2
        mock_get.assert_called_once_with(parser.base_url, timeout=30)

    @patch('parser.codeforces_parser.requests.Session.get')
    def test_fetch_problems_api_error(self, mock_get, parser, sample_api_error_data):
        """Тест обработки ошибки API"""
        mock_response = Mock()
        mock_response.json.return_value = sample_api_error_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = parser.fetch_problems()

        assert result is None

    @patch('parser.codeforces_parser.requests.Session.get')
    def test_fetch_problems_request_exception(self, mock_get, parser):
        """Тест обработки исключения запроса"""
        mock_get.side_effect = requests.exceptions.RequestException("Connection error")

        result = parser.fetch_problems()

        assert result is None

    @patch('parser.codeforces_parser.requests.Session.get')
    def test_fetch_problems_json_parse_error(self, mock_get, parser):
        """Тест обработки ошибки парсинга JSON"""
        mock_response = Mock()
        mock_response.json.side_effect = ValueError("Invalid JSON")
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        result = parser.fetch_problems()

        assert result is None

    @patch.object(CodeforcesParser, 'fetch_problems')
    def test_parse_and_save_problems_success(self, mock_fetch, parser, mock_db, sample_problems_data):
        """Тест успешного парсинга и сохранения задач"""
        mock_fetch.return_value = sample_problems_data['result']

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = parser.parse_and_save_problems(mock_db)

        assert result is True
        assert mock_db.commit.called
        assert mock_db.add.call_count >= 2

    @patch.object(CodeforcesParser, 'fetch_problems')
    def test_parse_and_save_problems_fetch_failed(self, mock_fetch, parser, mock_db):
        """Тест случая когда fetch_problems возвращает None"""
        mock_fetch.return_value = None

        result = parser.parse_and_save_problems(mock_db)

        assert result is False
        assert not mock_db.commit.called

    @patch.object(CodeforcesParser, 'fetch_problems')
    def test_parse_and_save_problems_exception(self, mock_fetch, parser, mock_db):
        """Тест обработки исключения в основном методе"""
        mock_fetch.side_effect = Exception("Unexpected error")

        result = parser.parse_and_save_problems(mock_db)

        assert result is False
        assert mock_db.rollback.called

    def test_create_new_problem_no_stats(self, parser, mock_db):
        """Тест создания задачи без статистики"""
        problem_data = {
            'contestId': 123,
            'index': 'C',
            'name': 'New Problem',
            'rating': 1700,
            'tags': []
        }

        parser._create_new_problem(mock_db, problem_data, None)

        mock_db.add.assert_called_once()
        added_problem = mock_db.add.call_args[0][0]
        assert added_problem.solved_count == 0

    def test_add_topics_to_problem_new_topics(self, parser, mock_db):
        """Тест добавления новых тем к задаче"""
        problem = Mock(spec=Problem)
        tags = ['dp', 'math', 'greedy']

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        parser._add_topics_to_problem(mock_db, problem, tags)

        assert mock_db.add.call_count == 3
        assert problem.topics.append.call_count == 3

    def test_add_topics_to_problem_existing_topics(self, parser, mock_db):
        """Тест добавления существующих тем к задаче"""
        problem = Mock(spec=Problem)
        tags = ['dp', 'math']
        existing_topic = Mock(spec=Topic)

        mock_db.query.return_value.filter_by.return_value.first.return_value = existing_topic

        parser._add_topics_to_problem(mock_db, problem, tags)

        assert mock_db.add.call_count == 0
        assert problem.topics.append.call_count == 2

    def test_add_topics_to_problem_empty_tags(self, parser, mock_db):
        """Тест добавления пустого списка тегов"""
        problem = Mock(spec=Problem)

        parser._add_topics_to_problem(mock_db, problem, [])

        assert not mock_db.add.called
        assert not problem.topics.append.called

    def test_update_existing_problem(self, parser):
        """Тест обновления существующей задачи"""
        problem = Mock(spec=Problem)
        problem_data = {
            'name': 'Updated Name',
            'rating': 1800,
            'tags': ['new', 'tags']
        }
        stats = {'solvedCount': 2000}

        parser._update_existing_problem(problem, problem_data, stats)

        assert problem.name == 'Updated Name'
        assert problem.rating == 1800
        assert problem.solved_count == 2000

    def test_update_existing_problem_no_stats(self, parser):
        """Тест обновления задачи без статистики"""
        problem = Mock(spec=Problem)
        problem.solved_count = 1000
        problem_data = {
            'name': 'Updated Name',
            'rating': 1800,
            'tags': ['new', 'tags']
        }

        parser._update_existing_problem(problem, problem_data, None)

        assert problem.name == 'Updated Name'
        assert problem.rating == 1800
        assert problem.solved_count == 1000

    @patch('parser.codeforces_parser.CodeforcesParser')
    def test_update_problems_success(self, mock_parser_class, mock_db):
        """Тест функции update_problems"""
        mock_parser = Mock()
        mock_parser.parse_and_save_problems.return_value = True
        mock_parser_class.return_value = mock_parser

        result = update_problems(mock_db)

        assert result is True
        mock_parser_class.assert_called_once()
        mock_parser.parse_and_save_problems.assert_called_once_with(mock_db)

    @patch('parser.codeforces_parser.CodeforcesParser')
    def test_update_problems_failure(self, mock_parser_class, mock_db):
        """Тест функции update_problems при ошибке"""
        mock_parser = Mock()
        mock_parser.parse_and_save_problems.return_value = False
        mock_parser_class.return_value = mock_parser

        result = update_problems(mock_db)

        assert result is False

    @patch('parser.codeforces_parser.requests.Session.get')
    def test_integration_parser_flow(self, mock_get, parser, mock_db, sample_problems_data):
        """Интеграционный тест полного потока парсера"""
        mock_response = Mock()
        mock_response.json.return_value = sample_problems_data
        mock_response.raise_for_status.return_value = None
        mock_get.return_value = mock_response

        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = parser.parse_and_save_problems(mock_db)

        assert result is True
        assert mock_get.called
        assert mock_db.commit.called

    @patch.object(CodeforcesParser, 'fetch_problems')
    def test_parse_and_save_problems_individual_problem_error(self, mock_fetch, parser, mock_db):
        """Тест обработки ошибок в отдельных задачах"""
        problematic_data = {
            'status': 'OK',
            'result': {
                'problems': [
                    {
                        'contestId': 1,
                        'index': 'A',
                        'name': 'Good Problem',
                        'rating': 1500,
                        'tags': ['dp']
                    },
                    {
                        'contestId': None,
                        'index': None,
                        'name': 'Bad Problem'
                    }
                ],
                'problemStatistics': []
            }
        }
        mock_fetch.return_value = problematic_data['result']
        mock_db.query.return_value.filter_by.return_value.first.return_value = None

        result = parser.parse_and_save_problems(mock_db)

        assert result is True
        assert mock_db.commit.called

    def test_parser_initialization(self, parser):
        """Тест инициализации парсера"""
        assert parser.base_url == config.CODEFORCES_URL
        assert parser.session.headers['User-Agent'] is not None

    @patch('parser.codeforces_parser.requests.Session')
    def test_session_headers(self, mock_session):
        """Тест установки заголовков сессии"""
        parser = CodeforcesParser()
        assert mock_session.return_value.headers.update.called
