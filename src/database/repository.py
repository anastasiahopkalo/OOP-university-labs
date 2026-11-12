"""Репозиторії прогресу: де і як зберігається ProgressTracker.

ProgressRepository (ABC)
├── JsonProgressRepository - JSON-файл (формат ЛР2)
└── SqlProgressRepository  - SQLite через SQLAlchemy ORM (ЛР3)

GUI працює лише з інтерфейсом ProgressRepository, тож сховище можна
замінити, не змінюючи панелі (поліморфізм).
"""
import json
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, List, Optional, Union

from sqlalchemy import delete, func, select

from src.core.analytics import ProgressTracker
from src.database.database import Database
from src.database.models import ExerciseAttempt, Student

DEFAULT_STUDENT = "Студент"


class ProgressRepository(ABC):
    """Сховище прогресу студентів."""

    @abstractmethod
    def list_students(self) -> List[str]:
        """Імена всіх студентів за алфавітом."""

    @abstractmethod
    def create_student(self, name: str) -> None:
        """Створює порожній профіль; ValueError, якщо ім'я порожнє або вже зайняте."""

    @abstractmethod
    def delete_student(self, name: str) -> None:
        """Видаляє профіль разом з усіма спробами (якщо його немає - нічого не робить)."""

    @abstractmethod
    def load(self, student_name: str = DEFAULT_STUDENT) -> ProgressTracker:
        """Прогрес студента; якщо профілю немає - він створюється."""

    @abstractmethod
    def save(self, tracker: ProgressTracker) -> None:
        """Зберігає весь прогрес студента tracker.student_name."""

    def has_student(self, name: str) -> bool:
        return name in self.list_students()

    def import_from(self, other: "ProgressRepository") -> int:
        """Копіює всіх студентів з іншого сховища. Повертає кількість перенесених спроб."""
        copied = 0
        for name in other.list_students():
            tracker = other.load(name)
            self.save(tracker)
            copied += tracker.total_attempts()
        return copied

    @staticmethod
    def _validate_name(name: str) -> str:
        name = (name or "").strip()
        if not name:
            raise ValueError("Ім'я студента не може бути порожнім")
        if len(name) > 100:
            raise ValueError("Ім'я студента задовге (максимум 100 символів)")
        return name


class JsonProgressRepository(ProgressRepository):
    """Усі студенти в одному JSON-файлі: {"students": {ім'я: tracker.to_dict()}}.

    Читає і старий формат ЛР2, де у файлі лежав один ProgressTracker.
    """

    def __init__(self, path: Union[str, Path]):
        self._path = Path(path)

    @property
    def path(self) -> Path:
        return self._path

    def _read(self) -> Dict[str, dict]:
        try:
            data = json.loads(self._path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}
        if not isinstance(data, dict):
            return {}
        if "students" in data:
            return dict(data["students"])
        if "exercises" in data:  # формат ЛР2
            return {data.get("student_name", DEFAULT_STUDENT): data}
        return {}

    def _write(self, students: Dict[str, dict]) -> None:
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(json.dumps({"students": students}, ensure_ascii=False, indent=2),
                              encoding="utf-8")

    def list_students(self) -> List[str]:
        return sorted(self._read())

    def create_student(self, name: str) -> None:
        name = self._validate_name(name)
        students = self._read()
        if name in students:
            raise ValueError(f"Студент {name!r} вже існує")
        students[name] = ProgressTracker(name).to_dict()
        self._write(students)

    def delete_student(self, name: str) -> None:
        students = self._read()
        if students.pop(name, None) is not None:
            self._write(students)

    def load(self, student_name: str = DEFAULT_STUDENT) -> ProgressTracker:
        data = self._read().get(student_name)
        if data is None:
            return ProgressTracker(student_name)
        try:
            tracker = ProgressTracker.from_dict(data)
        except (KeyError, TypeError, ValueError):
            return ProgressTracker(student_name)
        tracker.student_name = student_name
        return tracker

    def save(self, tracker: ProgressTracker) -> None:
        students = self._read()
        students[tracker.student_name] = tracker.to_dict()
        self._write(students)


class SqlProgressRepository(ProgressRepository):
    """Прогрес у реляційній БД через SQLAlchemy ORM."""

    def __init__(self, database: Database):
        self._db = database

    @property
    def database(self) -> Database:
        return self._db

    def list_students(self) -> List[str]:
        with self._db.session() as session:
            return list(session.scalars(select(Student.name).order_by(Student.name)))

    def create_student(self, name: str) -> None:
        name = self._validate_name(name)
        with self._db.session() as session:
            if self._find(session, name) is not None:
                raise ValueError(f"Студент {name!r} вже існує")
            session.add(Student(name=name))

    def delete_student(self, name: str) -> None:
        with self._db.session() as session:
            student = self._find(session, name)
            if student is not None:
                session.delete(student)

    def load(self, student_name: str = DEFAULT_STUDENT) -> ProgressTracker:
        with self._db.session() as session:
            student = self._find(session, student_name)
            if student is None:
                student = Student(name=self._validate_name(student_name))
                session.add(student)
            tracker = ProgressTracker(student.name)
            tracker.total_time = student.total_time or 0.0
            for attempt in student.attempts:
                tracker.completed_exercises.setdefault(attempt.exercise, []).append(attempt.to_record())
            return tracker

    def save(self, tracker: ProgressTracker) -> None:
        with self._db.session() as session:
            student = self._find(session, tracker.student_name)
            if student is None:
                student = Student(name=self._validate_name(tracker.student_name))
                session.add(student)
                session.flush()
            student.total_time = tracker.total_time
            # Набір спроб невеликий, тож простіше переписати його повністю
            session.execute(delete(ExerciseAttempt).where(ExerciseAttempt.student_id == student.id))
            session.add_all(
                ExerciseAttempt(student_id=student.id, exercise=name, passed=bool(a["passed"]),
                                score=int(a["score"]), time=float(a["time"]), timestamp=a["timestamp"])
                for name, attempts in tracker.completed_exercises.items()
                for a in attempts
            )
            session.expire(student, ["attempts"])

    def is_empty(self) -> bool:
        with self._db.session() as session:
            return session.scalar(select(func.count(Student.id))) == 0

    def leaderboard(self, limit: int = 10) -> List[tuple]:
        """[(ім'я, сума найкращих балів, кількість спроб)] за спаданням балів."""
        with self._db.session() as session:
            best = (select(ExerciseAttempt.student_id, ExerciseAttempt.exercise,
                           func.max(ExerciseAttempt.score).label("best"))
                    .group_by(ExerciseAttempt.student_id, ExerciseAttempt.exercise).subquery())
            attempts = (select(ExerciseAttempt.student_id, func.count().label("n"))
                        .group_by(ExerciseAttempt.student_id).subquery())
            query = (select(Student.name,
                            func.coalesce(func.sum(best.c.best), 0),
                            func.coalesce(func.max(attempts.c.n), 0))
                     .outerjoin(best, best.c.student_id == Student.id)
                     .outerjoin(attempts, attempts.c.student_id == Student.id)
                     .group_by(Student.id)
                     .order_by(func.coalesce(func.sum(best.c.best), 0).desc(), Student.name)
                     .limit(limit))
            return [tuple(row) for row in session.execute(query)]

    @staticmethod
    def _find(session, name: str) -> Optional[Student]:
        return session.scalar(select(Student).where(Student.name == name))


def migrate_json_to_sql(json_path: Union[str, Path], sql: SqlProgressRepository) -> int:
    """Одноразово переносить прогрес ЛР2 з JSON у порожню БД.

    Після імпорту файл перейменовується в *.imported, щоб не імпортувати двічі.
    Повертає кількість перенесених спроб.
    """
    json_path = Path(json_path)
    if not json_path.exists() or not sql.is_empty():
        return 0
    copied = sql.import_from(JsonProgressRepository(json_path))
    try:
        json_path.rename(json_path.with_name(json_path.name + ".imported"))
    except OSError:
        pass
    return copied
