import sys
import os
from database.models import Base, Problem, Topic, problem_topic_association

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))


class TestProblemModel:
    """Тесты для модели Problem"""

    def test_problem_creation(self):
        """Тест создания объекта Problem"""
        problem = Problem(
            contest_id=123,
            problem_index="A",
            name="Test Problem",
            rating=800,
            solved_count=1500
        )

        assert problem.contest_id == 123
        assert problem.problem_index == "A"
        assert problem.name == "Test Problem"
        assert problem.rating == 800
        assert problem.solved_count == 1500
        assert problem.topics == []

    def test_problem_full_code_property(self):
        """Тест свойства full_code"""
        problem = Problem(contest_id=123, problem_index="A")
        assert problem.full_code == "123A"

        problem2 = Problem(contest_id=456, problem_index="B")
        assert problem2.full_code == "456B"

    def test_problem_codeforces_url_property(self):
        """Тест свойства codeforces_url"""
        problem = Problem(contest_id=123, problem_index="A")
        expected_url = "https://codeforces.com/problemset/problem/123/A"
        assert problem.codeforces_url == expected_url

        problem2 = Problem(contest_id=456, problem_index="B")
        expected_url2 = "https://codeforces.com/problemset/problem/456/B"
        assert problem2.codeforces_url == expected_url2

    def test_problem_repr(self):
        """Тест строкового представления"""
        problem = Problem(
            contest_id=123,
            problem_index="A",
            name="Test Problem",
            rating=800
        )

        repr_str = repr(problem)
        assert "123A" in repr_str
        assert "Test Problem" in repr_str
        assert "800" in repr_str
        assert repr_str == "Problem(123A: Test Problem, rating: 800)"

    def test_problem_with_none_rating(self):
        """Тест задачи без рейтинга"""
        problem = Problem(
            contest_id=123,
            problem_index="A",
            name="Test Problem",
            rating=None
        )

        assert problem.rating is None
        assert "rating: None" in repr(problem)


class TestTopicModel:
    """Тесты для модели Topic"""

    def test_topic_creation(self):
        """Тест создания объекта Topic"""
        topic = Topic(name="math")

        assert topic.name == "math"
        assert topic.problems == []

    def test_topic_repr(self):
        """Тест строкового представления"""
        topic = Topic(name="dynamic programming")
        assert repr(topic) == "Topic(dynamic programming)"

    def test_topic_unique_name(self):
        """Тест что поле name уникально"""
        from sqlalchemy import inspect
        inspector = inspect(Topic)
        name_column = inspector.columns['name']
        assert name_column.unique is True


class TestProblemTopicRelationship:
    """Тесты для связи между Problem и Topic"""

    def test_many_to_many_relationship(self):
        """Тест связи многие-ко-многим"""
        problem1 = Problem(contest_id=123, problem_index="A", name="Problem A")
        problem2 = Problem(contest_id=124, problem_index="B", name="Problem B")

        topic_math = Topic(name="math")
        topic_graphs = Topic(name="graphs")

        problem1.topics.append(topic_math)
        problem1.topics.append(topic_graphs)
        problem2.topics.append(topic_math)

        assert len(problem1.topics) == 2
        assert topic_math in problem1.topics
        assert topic_graphs in problem1.topics
        assert len(problem2.topics) == 1
        assert topic_math in problem2.topics

        assert len(topic_math.problems) == 2
        assert problem1 in topic_math.problems
        assert problem2 in topic_math.problems
        assert len(topic_graphs.problems) == 1
        assert problem1 in topic_graphs.problems


class TestAssociationTable:
    """Тесты для ассоциативной таблицы"""

    def test_association_table_structure(self):
        """Тест структуры ассоциативной таблицы"""
        assert problem_topic_association.name == 'problem_topic_association'

        columns = problem_topic_association.columns
        assert 'problem_id' in columns
        assert 'topic_id' in columns

        problem_id_col = columns['problem_id']
        topic_id_col = columns['topic_id']

        assert len(problem_id_col.foreign_keys) == 1
        assert len(topic_id_col.foreign_keys) == 1

        problem_fk = list(problem_id_col.foreign_keys)[0]
        topic_fk = list(topic_id_col.foreign_keys)[0]

        assert problem_fk.column.table.name == 'problems'
        assert topic_fk.column.table.name == 'topics'


class TestBaseModel:
    """Тесты для базовой модели"""

    def test_base_metadata(self):
        """Тест что Base имеет метаданные"""
        assert hasattr(Base, 'metadata')
        assert Base.metadata is not None

    def test_tables_in_metadata(self):
        """Тест что таблицы присутствуют в метаданных"""
        tables = Base.metadata.tables
        assert 'problems' in tables
        assert 'topics' in tables
        assert 'problem_topic_association' in tables


class TestModelProperties:
    """Тесты дополнительных свойств моделей"""

    def test_problem_with_topics_repr(self):
        """Тест repr проблемы с темами"""
        problem = Problem(contest_id=123, problem_index="A", name="Test Problem")
        topic1 = Topic(name="math")
        topic2 = Topic(name="brute force")

        problem.topics = [topic1, topic2]

        repr_str = repr(problem)
        assert "123A" in repr_str
        assert "Test Problem" in repr_str

    def test_topic_with_problems_repr(self):
        """Тест repr темы с проблемами"""
        topic = Topic(name="math")
        problem1 = Problem(contest_id=123, problem_index="A", name="Problem A")
        problem2 = Problem(contest_id=124, problem_index="B", name="Problem B")

        topic.problems = [problem1, problem2]

        repr_str = repr(topic)
        assert "math" in repr_str


class TestModelConstraints:
    """Тесты ограничений моделей"""

    def test_problem_required_fields(self):
        """Тест обязательных полей Problem"""
        problem = Problem()

        from sqlalchemy import inspect
        inspector = inspect(Problem)

        contest_id_col = inspector.columns['contest_id']
        problem_index_col = inspector.columns['problem_index']
        name_col = inspector.columns['name']

        assert contest_id_col.nullable is False
        assert problem_index_col.nullable is False
        assert name_col.nullable is False

    def test_topic_required_fields(self):
        """Тест обязательных полей Topic"""
        from sqlalchemy import inspect
        inspector = inspect(Topic)

        name_col = inspector.columns['name']
        assert name_col.nullable is False


class TestModelIntegration:
    """Интеграционные тесты моделей"""

    def test_can_create_all_tables(self):
        """Тест что все таблицы могут быть созданы"""
        from sqlalchemy import create_engine

        test_engine = create_engine('sqlite:///:memory:')

        try:
            Base.metadata.create_all(test_engine)

            tables = Base.metadata.tables.keys()
            assert 'problems' in tables
            assert 'topics' in tables
            assert 'problem_topic_association' in tables

        finally:
            test_engine.dispose()

    def test_problem_topic_relationship_in_db(self):
        """Тест связи в реальной БД"""
        from sqlalchemy import create_engine
        from sqlalchemy.orm import sessionmaker

        test_engine = create_engine('sqlite:///:memory:')
        Base.metadata.create_all(test_engine)

        Session = sessionmaker(bind=test_engine)
        session = Session()

        try:
            problem = Problem(contest_id=123, problem_index="A", name="Test Problem")
            topic = Topic(name="math")

            problem.topics.append(topic)

            session.add(problem)
            session.add(topic)
            session.commit()

            saved_problem = session.query(Problem).first()
            saved_topic = session.query(Topic).first()

            assert len(saved_problem.topics) == 1
            assert saved_problem.topics[0].name == "math"
            assert len(saved_topic.problems) == 1
            assert saved_topic.problems[0].full_code == "123A"

        finally:
            session.close()
            test_engine.dispose()
