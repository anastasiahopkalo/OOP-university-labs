"""Тести досягнень і вкладки «Прогрес» (без дисплея)."""
import os
from datetime import datetime, timedelta

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PyQt5.QtWidgets")

from src.core.achievements import ACHIEVEMENTS, unlocked  # noqa: E402
from src.core.analytics import ProgressTracker  # noqa: E402
from src.core.exercise import ExerciseResult  # noqa: E402
from src.core.exercise_catalog import default_exercises  # noqa: E402
from src.gui.styles import DARK  # noqa: E402


def result(score):
    return ExerciseResult(score == 100, score, "", 0.1)


def titles(achievements):
    return {a.title for a in achievements}


class TestAchievements:
    def test_nothing_for_new_student(self):
        assert unlocked(ProgressTracker("x"), 7) == []

    def test_first_steps(self):
        t = ProgressTracker("x")
        t.record_attempt("A", result(50))
        assert titles(unlocked(t, 7)) == {"Перший крок"}
        t.record_attempt("A", result(100))
        assert "Перший розв'язок" in titles(unlocked(t, 7))
        assert "З першої спроби" not in titles(unlocked(t, 7))

    def test_first_try_and_all_solved(self):
        t = ProgressTracker("x")
        t.record_attempt("A", result(100))
        t.record_attempt("B", result(100))
        got = titles(unlocked(t, 2))
        assert {"З першої спроби", "Половина шляху", "Майстер алгоритмів"} <= got

    def test_persistence_and_streak(self):
        t = ProgressTracker("x")
        now = datetime.now()
        for i in range(10):
            t.record_attempt("A", result(10), now - timedelta(days=i % 3))
        got = titles(unlocked(t, 7))
        assert {"Наполегливість", "Серія 3 дні"} <= got

    def test_unique_titles(self):
        assert len(titles(ACHIEVEMENTS)) == len(ACHIEVEMENTS)


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def panel(app):
    from src.gui.panels.dashboard_panel import DashboardPanel
    tracker = ProgressTracker("Тест")
    tracker.record_attempt("Максимальний елемент", result(100))
    tracker.record_attempt("Бінарний пошук", result(50))
    return DashboardPanel(tracker, default_exercises())


class TestDashboardPanel:
    def test_cards(self, panel):
        assert panel.solved_card.value_label.text() == "1 / 7"
        assert panel.attempts_card.value_label.text() == "2"
        assert panel.average_card.value_label.text() == "75"
        assert panel.success_card.value_label.text() == "50%"

    def test_achievements_list(self, panel):
        assert panel.achievements.count() == len(ACHIEVEMENTS)
        assert panel.achievements_title.text().startswith("Досягнення: 3 з")

    def test_chart_has_two_axes(self, panel):
        assert len(panel.chart.figure.axes) == 2

    def test_refresh_after_new_attempt(self, panel):
        panel.tracker.record_attempt("Бінарний пошук", result(100))
        panel.refresh()
        assert panel.solved_card.value_label.text() == "2 / 7"

    def test_reset_emits_signal(self, panel):
        fired = []
        panel.progressReset.connect(lambda: fired.append(True))
        panel.reset_progress()
        assert fired == [True]
        assert panel.attempts_card.value_label.text() == "0"

    def test_theme(self, panel):
        panel.set_theme(DARK)
        assert panel.chart.figure.get_facecolor()[:3] != (1.0, 1.0, 1.0)

    def test_empty_tracker(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        empty = DashboardPanel(ProgressTracker("x"), default_exercises())
        assert empty.solved_card.value_label.text() == "0 / 7"


def test_main_window_reset_saves_file(app, tmp_path):
    from src.gui.main_window import MainWindow
    path = tmp_path / "p.json"
    tracker = ProgressTracker("x")
    tracker.record_attempt("Максимальний елемент", result(100))
    tracker.save(path)
    window = MainWindow(progress_path=path)
    assert window.dashboard_panel.solved_card.value_label.text() == "1 / 7"
    window.dashboard_panel.reset_progress()
    assert ProgressTracker.load(path).total_attempts() == 0
