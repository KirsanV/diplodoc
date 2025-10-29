import requests
import logging
from typing import List, Dict, Any, Optional
from sqlalchemy.orm import Session
from database.models import Problem, Topic
from config.config import config

logger = logging.getLogger(__name__)


class CodeforcesParser:
    """Парсер задач с Codeforces"""

    def __init__(self):
        self.base_url = config.CODEFORCES_URL
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
        })

    def fetch_problems(self) -> Optional[Dict[str, Any]]:
        """Получение задач через Codeforces API"""
        try:
            logger.info("Fetching problems from Codeforces API...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            data = response.json()

            if data['status'] != 'OK':
                logger.error(f"API returned error: {data.get('comment', 'Unknown error')}")
                return None

            logger.info(f"Successfully fetched {len(data['result']['problems'])} problems")
            return data['result']

        except requests.exceptions.RequestException as e:
            logger.error(f"Error fetching problems: {e}")
            return None
        except ValueError as e:
            logger.error(f"Error parsing JSON: {e}")
            return None

    def parse_and_save_problems(self, db: Session) -> bool:
        """Парсинг и сохранение задач в базу данных"""
        try:
            result = self.fetch_problems()
            if not result:
                return False

            problems_data = result['problems']
            problem_statistics = result.get('problemStatistics', [])

            stats_dict = {
                f"{stat['contestId']}{stat['index']}": stat
                for stat in problem_statistics
            }

            processed_count = 0
            skipped_count = 0

            for problem_data in problems_data:
                try:
                    problem_key = f"{problem_data['contestId']}{problem_data['index']}"

                    existing_problem = db.query(Problem).filter_by(
                        contest_id=problem_data['contestId'],
                        problem_index=problem_data['index']
                    ).first()

                    if existing_problem:
                        self._update_existing_problem(existing_problem, problem_data, stats_dict.get(problem_key))
                        skipped_count += 1
                    else:
                        self._create_new_problem(db, problem_data, stats_dict.get(problem_key))
                        processed_count += 1

                except Exception as e:
                    logger.warning(
                        f"Error processing problem {problem_data.get('contestId', '?')}"
                        f"{problem_data.get('index', '?')}: {e}")
                    continue

            db.commit()
            logger.info(
                f"Successfully processed {processed_count} new problems, updated {skipped_count} existing problems")
            return True

        except Exception as e:
            logger.error(f"Error in parse_and_save_problems: {e}")
            db.rollback()
            return False

    def _update_existing_problem(self, problem: Problem, problem_data: Dict, stats: Optional[Dict]):
        """Обновление существующей задачи"""
        problem.name = problem_data.get('name', problem.name)
        problem.rating = problem_data.get('rating', problem.rating)

        if stats:
            problem.solved_count = stats.get('solvedCount', problem.solved_count)

        self._update_problem_topics(problem, problem_data.get('tags', []))

    def _create_new_problem(self, db: Session, problem_data: Dict, stats: Optional[Dict]):
        """Создание новой задачи"""
        problem = Problem(
            contest_id=problem_data['contestId'],
            problem_index=problem_data['index'],
            name=problem_data['name'],
            rating=problem_data.get('rating'),
            solved_count=stats.get('solvedCount', 0) if stats else 0
        )

        self._add_topics_to_problem(db, problem, problem_data.get('tags', []))

        db.add(problem)

    def _add_topics_to_problem(self, db: Session, problem: Problem, tags: List[str]):
        """Добавление тем к задаче"""
        for tag_name in tags:
            if not tag_name:
                continue

            topic = db.query(Topic).filter_by(name=tag_name).first()
            if not topic:
                topic = Topic(name=tag_name)
                db.add(topic)
                db.flush()

            problem.topics.append(topic)

    def _update_problem_topics(self, problem: Problem, tags: List[str]):
        """Обновление тем задачи (упрощенная версия)"""
        pass


def update_problems(db: Session):
    """Функция для обновления задач (используется планировщиком)"""
    parser = CodeforcesParser()
    return parser.parse_and_save_problems(db)
