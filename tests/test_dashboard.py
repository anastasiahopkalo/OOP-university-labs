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


def test_main_window_reset_saves_to_repository(app, make_db):
    from src.gui.main_window import MainWindow
    from src.database import SqlProgressRepository
    repo = SqlProgressRepository(make_db())
    tracker = ProgressTracker("x")
    tracker.record_attempt("Максимальний елемент", result(100))
    repo.save(tracker)
    window = MainWindow(repo, student="x")
    assert window.dashboard_panel.solved_card.value_label.text() == "1 / 7"
    window.dashboard_panel.reset_progress()
    assert repo.load("x").total_attempts() == 0


def test_main_window_switch_student(app, make_db):
    from src.gui.main_window import MainWindow
    from src.database import SqlProgressRepository
    repo = SqlProgressRepository(make_db())
    tracker = ProgressTracker("A")
    tracker.record_attempt("Максимальний елемент", result(100))
    repo.save(tracker)
    repo.create_student("B")
    window = MainWindow(repo, student="A")
    window.switch_student("B")
    assert window.student_name == "B"
    assert window.exercise_panel.tracker is window.tracker
    assert window.dashboard_panel.solved_card.value_label.text() == "0 / 7"
    window.switch_student("A")
    assert window.dashboard_panel.solved_card.value_label.text() == "1 / 7"


def test_main_window_picks_existing_student(app, make_db):
    from src.gui.main_window import MainWindow
    from src.database import SqlProgressRepository
    repo = SqlProgressRepository(make_db())
    repo.create_student("Єдиний")
    window = MainWindow(repo)
    assert window.student_name in repo.list_students()


class TestDashboardLab3:
    def test_sections(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        panel = DashboardPanel(ProgressTracker("Настя"), default_exercises())
        titles = [panel.sections.tabText(i) for i in range(panel.sections.count())]
        assert titles == ["Результати", "Граф знань", "Активність і рейтинг", "Порівняння алгоритмів"]
        assert "Настя" in panel.title_label.text()

    def test_knowledge_graph_and_recommendation(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        tracker = ProgressTracker("x")
        panel = DashboardPanel(tracker, default_exercises())
        assert "Масиви" in panel.recommendation_label.text()
        assert set(panel.knowledge_chart.positions) == set(panel.knowledge_graph.graph.nodes)
        tracker.record_attempt("Максимальний елемент", result(100))
        tracker.record_attempt("Розворот списку", result(100))
        panel.refresh()
        assert "Бінарний пошук" in panel.recommendation_label.text()

    def test_recommendation_when_all_solved(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        tracker = ProgressTracker("x")
        for e in default_exercises():
            tracker.record_attempt(e.title, result(100))
        panel = DashboardPanel(tracker, default_exercises())
        assert "Вправи всіх доступних тем розв'язано" in panel.recommendation_label.text()

    def test_activity_series(self):
        from datetime import date, datetime
        from src.gui.panels.dashboard_panel import ActivityChart
        tracker = ProgressTracker("x")
        tracker.record_attempt("A", result(10), datetime(2026, 11, 10, 9))
        tracker.record_attempt("A", result(20), datetime(2026, 11, 10, 10))
        tracker.record_attempt("A", result(30), datetime(2026, 10, 1, 10))  # поза вікном
        data = ActivityChart.series(tracker, today=date(2026, 11, 12))
        assert len(data) == 14
        assert data[-1] == (date(2026, 11, 12), 0)
        assert dict(data)[date(2026, 11, 10)] == 2
        assert sum(count for _, count in data) == 2

    def test_leaderboard(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        rows = [("Настя", 300, 5), ("x", 100, 2)]
        panel = DashboardPanel(ProgressTracker("x"), default_exercises(), leaderboard=lambda: rows)
        table = panel.leaderboard_table
        assert table.rowCount() == 2
        assert [table.item(0, c).text() for c in range(4)] == ["1", "Настя", "300", "5"]
        assert table.item(1, 1).font().bold()  # поточний студент виділений

    def test_leaderboard_hidden_without_database(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        panel = DashboardPanel(ProgressTracker("x"), default_exercises())
        assert panel.leaderboard_table.rowCount() == 0
        assert panel.leaderboard_table.parentWidget().isHidden()

    def test_leaderboard_error(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel

        def broken():
            raise RuntimeError("db down")
        panel = DashboardPanel(ProgressTracker("x"), default_exercises(), leaderboard=broken)
        assert "db down" in panel.leaderboard_title.text()

    def test_dark_theme(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        panel = DashboardPanel(ProgressTracker("x"), default_exercises())
        panel.set_theme(DARK)
        assert panel.knowledge_chart.status_colors()["mastered"] == DARK.done


class TestBenchmarkHistory:
    @staticmethod
    def run(algorithm, size, ms, kind="random", minute=0, run_id=None):
        from datetime import datetime
        from src.database import AlgorithmRun
        return AlgorithmRun(id=run_id, algorithm=algorithm, input_kind=kind, size=size,
                            mean_time=ms / 1000, timestamp=datetime(2026, 11, 12, 10, minute))

    def test_summarize_takes_latest_kind_and_largest_n(self):
        from src.gui.panels.dashboard_panel import BenchmarkHistoryChart
        runs = [
            self.run("BubbleSort", 100, 5, minute=1),
            self.run("BubbleSort", 800, 290, minute=1),
            self.run("MergeSort", 800, 9, minute=1),
            self.run("MergeSort", 800, 7, minute=5),              # той самий n, новіший замір
            self.run("QuickSort", 5000, 1, kind="sorted", minute=0),  # старіший тип даних
        ]
        kind, bars = BenchmarkHistoryChart.summarize(runs)
        assert kind == "random"
        assert bars == [("Merge Sort", pytest.approx(7), 800), ("Bubble Sort", pytest.approx(290), 800)]
        assert BenchmarkHistoryChart.summarize([]) == (None, [])

    def test_section_hidden_without_history(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        panel = DashboardPanel(ProgressTracker("x"), default_exercises())
        assert not panel.sections.isTabVisible(panel.history_tab_index)

    def test_section_with_runs(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        runs = [self.run("QuickSort", 500, 3), self.run("HeapSort", 500, 6)]
        panel = DashboardPanel(ProgressTracker("x"), default_exercises(), run_history=lambda: runs)
        assert panel.sections.isTabVisible(panel.history_tab_index)
        assert panel.sections.tabText(panel.history_tab_index) == "Порівняння алгоритмів"
        assert "Quick Sort" in panel.history_label.text()
        assert "2" in panel.history_label.text()
        panel.set_theme(DARK)

    def test_empty_and_error(self, app):
        from src.gui.panels.dashboard_panel import DashboardPanel
        panel = DashboardPanel(ProgressTracker("x"), default_exercises(), run_history=lambda: [])
        assert panel.history_label.text() == "Збережених замірів поки немає."

        def broken():
            raise RuntimeError("db down")
        panel = DashboardPanel(ProgressTracker("x"), default_exercises(), run_history=broken)
        assert "db down" in panel.history_label.text()


def test_benchmark_results_reach_dashboard(app, make_db):
    from src.gui.main_window import MainWindow
    from src.database import SqlProgressRepository
    window = MainWindow(SqlProgressRepository(make_db()), student="Настя")
    assert window.dashboard_panel.history_label.text() == "Збережених замірів поки немає."
    bench = window.benchmark_panel
    bench.set_selected_algorithms(["Merge Sort", "Quick Sort"])
    bench.min_size.setValue(10)
    bench.max_size.setValue(20)
    bench.points.setValue(2)
    bench.repeats.setValue(1)
    bench.start()
    assert bench.wait()
    app.processEvents()
    assert "Збережених замірів: 4" in window.dashboard_panel.history_label.text()
    assert {name for name, _, _ in window.dashboard_panel.history_chart.bars} == {"Merge Sort", "Quick Sort"}
    # в іншого студента своя історія
    window.repository.create_student("Даніїл")
    window.switch_student("Даніїл")
    assert window.dashboard_panel.history_label.text() == "Збережених замірів поки немає."
