from datetime import datetime, date, timedelta

import pytest

from src.core.analytics import ProgressTracker
from src.core.exercise import ExerciseResult


def result(score, passed=None):
    return ExerciseResult(passed if passed is not None else score == 100, score, "", 0.5)


@pytest.fixture
def tracker():
    t = ProgressTracker("Тест")
    base = datetime(2026, 10, 20, 12, 0)
    t.record_attempt("A", result(50), base)
    t.record_attempt("A", result(100), base + timedelta(hours=1))
    t.record_attempt("B", result(30), base + timedelta(days=1))
    t.record_attempt("C", result(0), base + timedelta(days=2))
    return t


def test_best_scores_and_solved(tracker):
    assert tracker.best_score("A") == 100
    assert tracker.best_score("missing") is None
    assert tracker.best_scores() == {"A": 100, "B": 30, "C": 0}
    assert tracker.solved_exercises() == ["A"]


def test_history_is_chronological(tracker):
    assert [r["exercise"] for r in tracker.history()] == ["A", "A", "B", "C"]
    assert tracker.total_attempts() == 4


def test_averages(tracker):
    assert tracker.average_score() == 45
    assert tracker.success_rate() == 0.25
    assert tracker.total_time == 2.0


def test_statistics_keep_old_keys(tracker):
    stats = tracker.get_statistics()
    assert stats["completed"] == 1  # остання спроба A успішна, B і C - ні
    assert {"student", "completed", "total", "completion_rate", "attempts"} <= set(stats)


def test_daily_activity_and_streak(tracker):
    assert tracker.daily_activity() == {date(2026, 10, 20): 2, date(2026, 10, 21): 1, date(2026, 10, 22): 1}
    assert tracker.streak_days(today=date(2026, 10, 22)) == 3
    assert tracker.streak_days(today=date(2026, 10, 23)) == 3  # сьогодні ще не займались
    assert tracker.streak_days(today=date(2026, 10, 25)) == 0
    assert ProgressTracker("x").streak_days() == 0


def test_save_and_load(tracker, tmp_path):
    path = tmp_path / "sub" / "progress.json"
    tracker.save(path)
    loaded = ProgressTracker.load(path)
    assert loaded.student_name == "Тест"
    assert loaded.history() == tracker.history()
    assert loaded.total_time == tracker.total_time


def test_load_missing_or_broken(tmp_path):
    assert ProgressTracker.load(tmp_path / "nope.json").total_attempts() == 0
    broken = tmp_path / "broken.json"
    broken.write_text("{not json")
    assert ProgressTracker.load(broken, "Хтось").student_name == "Хтось"
