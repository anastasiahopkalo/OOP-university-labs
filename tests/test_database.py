"""Тести шару SQLAlchemy: моделі, репозиторії прогресу, міграція з JSON."""
from datetime import datetime, timedelta

import pytest
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from src.core.analytics import ProgressTracker
from src.core.exercise import ExerciseResult
from src.database import (
    AlgorithmRun, Database, ExerciseAttempt, JsonProgressRepository, SqlProgressRepository,
    Student, migrate_json_to_sql,
)

BASE = datetime(2026, 11, 10, 9, 0)


def result(score, passed=None):
    return ExerciseResult(passed if passed is not None else score == 100, score, "", 0.25)


def sample_tracker(name="Даніїл"):
    tracker = ProgressTracker(name)
    tracker.record_attempt("A", result(40), BASE)
    tracker.record_attempt("A", result(100), BASE + timedelta(hours=1))
    tracker.record_attempt("B", result(70), BASE + timedelta(days=1))
    return tracker


@pytest.fixture
def db():
    database = Database()
    yield database
    database.dispose()


@pytest.fixture
def sql(db):
    return SqlProgressRepository(db)


@pytest.fixture
def json_repo(tmp_path):
    return JsonProgressRepository(tmp_path / "progress.json")


class TestModels:
    def test_tables_created(self, db):
        from sqlalchemy import inspect
        assert {"students", "exercise_attempts", "algorithm_runs"} <= set(inspect(db.engine).get_table_names())

    def test_relationship_and_total_score(self, db):
        with db.session() as s:
            student = Student(name="Настя")
            student.attempts = [
                ExerciseAttempt(exercise="A", score=50, timestamp=BASE),
                ExerciseAttempt(exercise="A", score=90, timestamp=BASE + timedelta(1)),
                ExerciseAttempt(exercise="B", score=30, timestamp=BASE),
            ]
            s.add(student)
        with db.session() as s:
            student = s.scalar(select(Student))
            assert student.total_score == 120
            assert student.attempts[-1].score == 90  # спроби впорядковані за часом
            assert "Настя" in repr(student)

    def test_unique_name(self, db):
        with pytest.raises(IntegrityError):
            with db.session() as s:
                s.add_all([Student(name="X"), Student(name="X")])

    def test_cascade_delete(self, db):
        with db.session() as s:
            s.add(Student(name="X", attempts=[ExerciseAttempt(exercise="A", score=1)],
                          runs=[AlgorithmRun(algorithm="Q", input_kind="random", size=10, mean_time=0.1)]))
        with db.session() as s:
            s.delete(s.scalar(select(Student)))
        with db.session() as s:
            assert s.scalars(select(ExerciseAttempt)).all() == []
            assert s.scalars(select(AlgorithmRun)).all() == []

    def test_foreign_keys_enforced(self, db):
        with pytest.raises(IntegrityError):
            with db.session() as s:
                s.add(ExerciseAttempt(student_id=999, exercise="A"))

    def test_session_rolls_back_on_error(self, db):
        with pytest.raises(RuntimeError):
            with db.session() as s:
                s.add(Student(name="ghost"))
                s.flush()
                raise RuntimeError
        with db.session() as s:
            assert s.scalars(select(Student)).all() == []

    def test_file_database(self, tmp_path):
        path = tmp_path / "nested" / "codelearn.db"
        Database.from_path(path).dispose()
        assert path.exists()


@pytest.fixture(params=["sql", "json"])
def repo(request, sql, json_repo):
    """Обидві реалізації мають поводитися однаково (поліморфізм)."""
    return sql if request.param == "sql" else json_repo


class TestRepositoryContract:
    def test_round_trip(self, repo):
        repo.save(sample_tracker())
        loaded = repo.load("Даніїл")
        assert loaded.history() == sample_tracker().history()
        assert loaded.total_time == pytest.approx(0.75)
        assert loaded.best_scores() == {"A": 100, "B": 70}

    def test_save_overwrites(self, repo):
        tracker = sample_tracker()
        repo.save(tracker)
        tracker.completed_exercises.clear()
        tracker.total_time = 0
        repo.save(tracker)
        assert repo.load("Даніїл").total_attempts() == 0

    def test_students_are_separate(self, repo):
        repo.save(sample_tracker("Б"))
        repo.create_student("А")
        assert repo.list_students() == ["А", "Б"]
        assert repo.load("А").total_attempts() == 0
        assert repo.load("Б").total_attempts() == 3
        assert repo.has_student("А")

    def test_create_validation(self, repo):
        repo.create_student("  Олег  ")
        assert repo.list_students() == ["Олег"]
        with pytest.raises(ValueError):
            repo.create_student("Олег")
        with pytest.raises(ValueError):
            repo.create_student("   ")
        with pytest.raises(ValueError):
            repo.create_student("x" * 101)

    def test_delete(self, repo):
        repo.save(sample_tracker())
        repo.delete_student("Даніїл")
        repo.delete_student("нема такого")
        assert repo.list_students() == []

    def test_load_missing_student_is_empty(self, repo):
        assert repo.load("Новий").total_attempts() == 0


class TestSqlRepository:
    def test_load_creates_student(self, sql):
        assert sql.is_empty()
        sql.load("Новий")
        assert sql.list_students() == ["Новий"]

    def test_leaderboard(self, sql):
        sql.save(sample_tracker("A"))          # 100 + 70
        weak = ProgressTracker("B")
        weak.record_attempt("A", result(10), BASE)
        sql.save(weak)
        sql.create_student("C")
        assert sql.leaderboard() == [("A", 170, 3), ("B", 10, 1), ("C", 0, 0)]
        assert len(sql.leaderboard(limit=1)) == 1

    def test_import_from_json(self, sql, json_repo):
        json_repo.save(sample_tracker("X"))
        json_repo.save(sample_tracker("Y"))
        assert sql.import_from(json_repo) == 6
        assert sql.list_students() == ["X", "Y"]


class TestJsonRepository:
    def test_reads_lab2_format(self, tmp_path):
        path = tmp_path / "progress.json"
        sample_tracker("Старий").save(path)  # формат ЛР2: один трекер у файлі
        repo = JsonProgressRepository(path)
        assert repo.list_students() == ["Старий"]
        assert repo.load("Старий").total_attempts() == 3

    @pytest.mark.parametrize("content", ["not json", "[1, 2]", '{"other": 1}'])
    def test_broken_file_is_empty(self, tmp_path, content):
        path = tmp_path / "progress.json"
        path.write_text(content, encoding="utf-8")
        assert JsonProgressRepository(path).list_students() == []

    def test_broken_student_record(self, tmp_path):
        path = tmp_path / "progress.json"
        path.write_text('{"students": {"X": {"exercises": {"A": [{"bad": 1}]}}}}', encoding="utf-8")
        assert JsonProgressRepository(path).load("X").total_attempts() == 0


class TestMigration:
    def test_migrates_once(self, sql, tmp_path):
        path = tmp_path / "progress.json"
        sample_tracker("Студент").save(path)
        assert migrate_json_to_sql(path, sql) == 3
        assert not path.exists()
        assert (tmp_path / "progress.json.imported").exists()
        assert sql.load("Студент").best_score("A") == 100
        assert migrate_json_to_sql(path, sql) == 0

    def test_skips_when_db_not_empty(self, sql, tmp_path):
        path = tmp_path / "progress.json"
        sample_tracker().save(path)
        sql.create_student("Хтось")
        assert migrate_json_to_sql(path, sql) == 0
        assert path.exists()

    def test_no_file(self, sql, tmp_path):
        assert migrate_json_to_sql(tmp_path / "none.json", sql) == 0
