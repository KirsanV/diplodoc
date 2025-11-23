import pytest
import sys
import os
from unittest.mock import Mock
from sqlalchemy.orm import Session
from sqlalchemy import and_, or_
from services.task_services import TaskService
from database.models import Problem, Topic
import logging

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

logger = logging.getLogger(__name__)


class TestTaskService:
    """Тесты для TaskService"""

    @pytest.fixture
    def mock_db(self):
        return Mock(spec=Session)

    @pytest.fixture
    def sample_problems(self):
        return [
            Mock(spec=Problem, contest_id=1, problem_index='A', name='Problem A', rating=1500),
            Mock(spec=Problem, contest_id=2, problem_index='B', name='Problem B', rating=1600),
            Mock(spec=Problem, contest_id=3, problem_index='C', name='Problem C', rating=1500)
        ]

    @pytest.fixture
    def sample_topics(self):
        return [
            Mock(spec=Topic, name='dp'),
            Mock(spec=Topic, name='math'),
            Mock(spec=Topic, name='greedy')
        ]

    def test_get_problems_by_filters_no_filters(self, mock_db, sample_problems):
        """Тест получения задач без фильтров"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = sample_problems[:2]
        result = TaskService.get_problems_by_filters(mock_db)
        mock_db.query.assert_called_once_with(Problem)
        mock_query.distinct.assert_called_once_with(Problem.contest_id)
        mock_query.limit.assert_called_once_with(10)
        mock_query.all.assert_called_once()
        assert len(result) == 2

    def test_get_problems_by_filters_custom_limit(self, mock_db):
        """Тест получения задач с кастомным лимитом"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        TaskService.get_problems_by_filters(mock_db, limit=20)
        mock_query.limit.assert_called_once_with(20)

    def test_search_problems_by_name(self, mock_db, sample_problems):
        """Тест поиска задач по названию"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_problems[0]]
        result = TaskService.search_problems(mock_db, "Problem A")
        mock_query.filter.assert_called_once()
        filter_call = mock_query.filter.call_args[0][0]
        assert isinstance(filter_call, type(or_()))
        mock_query.limit.assert_called_once_with(20)
        assert len(result) == 1

    def test_search_problems_by_index(self, mock_db, sample_problems):
        """Тест поиска задач по индексу"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_problems[0]]
        result = TaskService.search_problems(mock_db, "A")
        mock_query.filter.assert_called_once()
        mock_query.limit.assert_called_once_with(20)
        assert len(result) == 1

    def test_search_problems_by_full_code(self, mock_db, sample_problems):
        """Тест поиска задач по полному коду"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_problems[0]]
        result = TaskService.search_problems(mock_db, "1A")
        mock_query.filter.assert_called_once()
        filter_call = mock_query.filter.call_args[0][0]
        assert hasattr(filter_call, 'clauses'), "Filter should have multiple clauses"
        assert len(filter_call.clauses) >= 2, "Should have at least 2 search conditions"
        assert len(result) == 1

    def test_search_problems_empty_result(self, mock_db):
        """Тест поиска задач без результатов"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        result = TaskService.search_problems(mock_db, "nonexistent")

        assert len(result) == 0

    def test_search_problems_case_insensitive(self, mock_db, sample_problems):
        """Тест регистронезависимого поиска"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_problems[0]]
        result = TaskService.search_problems(mock_db, "problem a")
        mock_query.filter.assert_called_once()
        assert len(result) == 1

    def test_get_available_ratings_with_none(self, mock_db):
        """Тест получения сложностей с исключением None"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [(1500,), (None,), (1600,)]
        result = TaskService.get_available_ratings(mock_db)

        assert result == [1500, 1600]

    def test_get_available_ratings_empty(self, mock_db):
        """Тест получения пустого списка сложностей"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        result = TaskService.get_available_ratings(mock_db)

        assert result == []

    def test_get_available_topics(self, mock_db, sample_topics):
        """Тест получения доступных тем"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = [('dp',), ('math',), ('greedy',)]
        result = TaskService.get_available_topics(mock_db)
        mock_db.query.assert_called_once_with(Topic.name)
        mock_query.distinct.assert_called_once()
        mock_query.order_by.assert_called_once_with(Topic.name)
        assert result == ['dp', 'math', 'greedy']

    def test_get_available_topics_empty(self, mock_db):
        """Тест получения пустого списка тем"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.order_by.return_value = mock_query
        mock_query.all.return_value = []
        result = TaskService.get_available_topics(mock_db)

        assert result == []

    def test_get_problem_by_code_found(self, mock_db, sample_problems):
        """Тест получения задачи по коду (найдена)"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = sample_problems[0]
        result = TaskService.get_problem_by_code(mock_db, 1, 'A')
        mock_db.query.assert_called_once_with(Problem)
        mock_query.filter.assert_called_once()
        filter_call = mock_query.filter.call_args[0][0]
        assert isinstance(filter_call, type(and_()))
        mock_query.first.assert_called_once()
        assert result == sample_problems[0]

    def test_get_problem_by_code_not_found(self, mock_db):
        """Тест получения задачи по коду (не найдена)"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        result = TaskService.get_problem_by_code(mock_db, 999, 'Z')

        assert result is None

    def test_get_problem_by_code_conditions(self, mock_db):
        """Тест условий фильтрации по коду задачи"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.first.return_value = None
        TaskService.get_problem_by_code(mock_db, 123, 'D')
        filter_call = mock_query.filter.call_args[0][0]
        assert len(filter_call.clauses) == 2
        assert any('contest_id' in str(clause) for clause in filter_call.clauses)
        assert any('problem_index' in str(clause) for clause in filter_call.clauses)

    def test_combined_filters_integration(self, mock_db, sample_problems):
        """Интеграционный тест комбинированных фильтров"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.join.return_value = mock_query
        mock_query.distinct.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = [sample_problems[0]]

        result = TaskService.get_problems_by_filters(
            mock_db,
            rating=1500,
            topic='dp',
            limit=5
        )
        assert len(result) == 1
        assert mock_query.filter.call_count >= 2
        assert mock_query.join.called

    def test_search_with_special_characters(self, mock_db):
        """Тест поиска со специальными символами"""
        mock_query = Mock()
        mock_db.query.return_value = mock_query
        mock_query.filter.return_value = mock_query
        mock_query.limit.return_value = mock_query
        mock_query.all.return_value = []
        result = TaskService.search_problems(mock_db, "test%_problem")
        mock_query.filter.assert_called_once()
        assert len(result) == 0
