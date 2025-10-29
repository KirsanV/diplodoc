from typing import List, Optional
from sqlalchemy.orm import Session
from sqlalchemy import and_, func, or_
from database.models import Problem, Topic


class TaskService:
    """Сервис для работы с задачами"""

    @staticmethod
    def get_problems_by_filters(
            db: Session,
            rating: Optional[int] = None,
            topic: Optional[str] = None,
            limit: int = 10
    ) -> List[Problem]:
        """Получение задач по фильтрам сложности и темы"""
        query = db.query(Problem)

        if rating:
            query = query.filter(Problem.rating == rating)

        if topic:
            query = query.join(Problem.topics).filter(Topic.name == topic)

        query = query.distinct(Problem.contest_id)

        return query.limit(limit).all()

    @staticmethod
    def search_problems(db: Session, search_query: str) -> List[Problem]:
        """Поиск задач по названию или коду"""
        search_term = f"%{search_query}%"
        return db.query(Problem).filter(
            or_(
                Problem.name.ilike(search_term),
                Problem.problem_index.ilike(search_term),
                func.concat(Problem.contest_id, Problem.problem_index).ilike(search_term)
            )
        ).limit(20).all()

    @staticmethod
    def get_available_ratings(db: Session) -> List[int]:
        """Получение списка доступных сложностей"""
        ratings = db.query(Problem.rating).filter(
            Problem.rating.isnot(None)
        ).distinct().order_by(Problem.rating).all()

        return [rating[0] for rating in ratings if rating[0] is not None]

    @staticmethod
    def get_available_topics(db: Session) -> List[str]:
        """Получение списка доступных тем"""
        topics = db.query(Topic.name).distinct().order_by(Topic.name).all()
        return [topic[0] for topic in topics]

    @staticmethod
    def get_problem_by_code(db: Session, contest_id: int, problem_index: str) -> Optional[Problem]:
        """Получение задачи по коду"""
        return db.query(Problem).filter(
            and_(
                Problem.contest_id == contest_id,
                Problem.problem_index == problem_index
            )
        ).first()
