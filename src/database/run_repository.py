"""Збереження результатів бенчмарку в таблиці algorithm_runs."""
from typing import List, Optional, Sequence

from sqlalchemy import delete, select

from src.core.benchmark import BenchmarkResult
from src.database.database import Database
from src.database.models import AlgorithmRun, Student


class AlgorithmRunRepository:
    def __init__(self, database: Database):
        self._db = database

    def save(self, results: Sequence[BenchmarkResult], student_name: Optional[str] = None) -> int:
        """Записує результати; якщо студента вказано, прив'язує до нього. Повертає кількість рядків."""
        with self._db.session() as session:
            student_id = None
            if student_name:
                student = session.scalar(select(Student).where(Student.name == student_name))
                student_id = student.id if student is not None else None
            session.add_all(
                AlgorithmRun(student_id=student_id, algorithm=r.algorithm, input_kind=r.input_kind,
                             size=r.size, mean_time=r.mean_time, std_time=r.std_time,
                             comparisons=int(round(r.comparisons)), swaps=int(round(r.swaps)))
                for r in results
            )
        return len(results)

    def history(self, algorithm: Optional[str] = None, input_kind: Optional[str] = None,
                student_name: Optional[str] = None) -> List[AlgorithmRun]:
        query = select(AlgorithmRun).order_by(AlgorithmRun.timestamp, AlgorithmRun.id)
        if algorithm:
            query = query.where(AlgorithmRun.algorithm == algorithm)
        if input_kind:
            query = query.where(AlgorithmRun.input_kind == input_kind)
        if student_name:
            query = query.join(Student).where(Student.name == student_name)
        with self._db.session() as session:
            return list(session.scalars(query))

    def count(self) -> int:
        return len(self.history())

    def clear(self) -> None:
        with self._db.session() as session:
            session.execute(delete(AlgorithmRun))
