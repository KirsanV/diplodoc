from sqlalchemy import Column, Integer, String, Table, ForeignKey
from sqlalchemy.orm import relationship, declarative_base

Base = declarative_base()

problem_topic_association = Table(
    'problem_topic_association',
    Base.metadata,
    Column('problem_id', Integer, ForeignKey('problems.id')),
    Column('topic_id', Integer, ForeignKey('topics.id'))
)


class Problem(Base):
    """Модель задачи Codeforces"""
    __tablename__ = 'problems'

    id = Column(Integer, primary_key=True, autoincrement=True)
    contest_id = Column(Integer, nullable=False)
    problem_index = Column(String(10), nullable=False)
    name = Column(String(500), nullable=False)
    rating = Column(Integer)
    solved_count = Column(Integer, default=0)

    topics = relationship("Topic", secondary=problem_topic_association, back_populates="problems")

    def __repr__(self):
        return f"Problem({self.contest_id}{self.problem_index}: {self.name}, rating: {self.rating})"

    @property
    def full_code(self):
        """Полный код задачи (например: 123A)"""
        return f"{self.contest_id}{self.problem_index}"

    @property
    def codeforces_url(self):
        """URL задачи на Codeforces"""
        return f"https://codeforces.com/problemset/problem/{self.contest_id}/{self.problem_index}"


class Topic(Base):
    """Модель темы задачи"""
    __tablename__ = 'topics'

    id = Column(Integer, primary_key=True, autoincrement=True)
    name = Column(String(100), unique=True, nullable=False)

    problems = relationship("Problem", secondary=problem_topic_association, back_populates="topics")

    def __repr__(self):
        return f"Topic({self.name})"
