"""ORM-моделі SQLAlchemy (ЛР3).

Схема:
    students            - профілі студентів
    exercise_attempts   - кожна спроба розв'язати вправу (належить студенту)
    algorithm_runs      - результати бенчмарку алгоритмів сортування
"""
from datetime import datetime
from typing import List, Optional

from sqlalchemy import DateTime, Float, ForeignKey, Integer, String, Boolean
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    """Спільна база для всіх моделей - через неї створюються таблиці."""


class Student(Base):
    __tablename__ = "students"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    name: Mapped[str] = mapped_column(String(100), unique=True, nullable=False)
    joined_date: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)
    total_time: Mapped[float] = mapped_column(Float, default=0.0)

    attempts: Mapped[List["ExerciseAttempt"]] = relationship(
        back_populates="student", cascade="all, delete-orphan",
        order_by="ExerciseAttempt.timestamp")
    runs: Mapped[List["AlgorithmRun"]] = relationship(
        back_populates="student", cascade="all, delete-orphan")

    @property
    def total_score(self) -> int:
        """Сума найкращих балів за кожну вправу."""
        best: dict = {}
        for attempt in self.attempts:
            best[attempt.exercise] = max(best.get(attempt.exercise, 0), attempt.score)
        return sum(best.values())

    def __repr__(self) -> str:
        return f"Student(id={self.id}, name={self.name!r})"


class ExerciseAttempt(Base):
    __tablename__ = "exercise_attempts"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[int] = mapped_column(ForeignKey("students.id"), index=True)
    exercise: Mapped[str] = mapped_column(String(200), nullable=False)
    passed: Mapped[bool] = mapped_column(Boolean, default=False)
    score: Mapped[int] = mapped_column(Integer, default=0)
    time: Mapped[float] = mapped_column(Float, default=0.0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student: Mapped[Student] = relationship(back_populates="attempts")

    def to_record(self) -> dict:
        """Формат запису, з яким працює ProgressTracker."""
        return {"passed": self.passed, "score": self.score,
                "time": self.time, "timestamp": self.timestamp}

    def __repr__(self) -> str:
        return f"ExerciseAttempt({self.exercise!r}, score={self.score})"


class AlgorithmRun(Base):
    __tablename__ = "algorithm_runs"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    student_id: Mapped[Optional[int]] = mapped_column(ForeignKey("students.id"), nullable=True)
    algorithm: Mapped[str] = mapped_column(String(100), nullable=False)
    input_kind: Mapped[str] = mapped_column(String(50), nullable=False)
    size: Mapped[int] = mapped_column(Integer, nullable=False)
    mean_time: Mapped[float] = mapped_column(Float, nullable=False)
    std_time: Mapped[float] = mapped_column(Float, default=0.0)
    comparisons: Mapped[int] = mapped_column(Integer, default=0)
    swaps: Mapped[int] = mapped_column(Integer, default=0)
    timestamp: Mapped[datetime] = mapped_column(DateTime, default=datetime.now)

    student: Mapped[Optional[Student]] = relationship(back_populates="runs")

    def __repr__(self) -> str:
        return f"AlgorithmRun({self.algorithm!r}, n={self.size}, {self.mean_time:.4f}s)"
