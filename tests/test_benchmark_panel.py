"""GUI-тести вкладки «Порівняння» (headless)."""
import os

import numpy as np
import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PyQt5.QtWidgets")

from src.core.benchmark import BenchmarkResult  # noqa: E402
from src.database import AlgorithmRunRepository, SqlProgressRepository  # noqa: E402
from src.gui.styles import DARK  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def panel(app):
    from src.gui.panels.benchmark_panel import BenchmarkPanel
    p = BenchmarkPanel()
    p.min_size.setValue(20)
    p.max_size.setValue(60)
    p.points.setValue(3)
    p.repeats.setValue(1)
    return p


def run_and_wait(app, panel):
    panel.start()
    assert panel.wait()
    app.processEvents()


def test_defaults(panel):
    assert panel.selected_algorithms() == ["Bubble Sort", "Insertion Sort", "Merge Sort",
                                           "Quick Sort", "Heap Sort"]
    assert panel.current_metric == "time"
    assert panel.table.rowCount() == 0


def test_build_benchmark(panel):
    panel.set_selected_algorithms(["Merge Sort"])
    assert panel.build_benchmark().total_runs == 3
    panel.set_selected_algorithms([])
    with pytest.raises(ValueError):
        panel.build_benchmark()


def test_start_without_algorithms_shows_error(panel):
    panel.set_selected_algorithms([])
    panel.start()
    assert not panel.running
    assert "алгоритм" in panel.status.text()


def test_run_fills_chart_and_table(app, panel):
    panel.set_selected_algorithms(["Bubble Sort", "Merge Sort"])
    run_and_wait(app, panel)
    assert len(panel.results) == 6
    assert panel.table.rowCount() == 2
    assert panel.progress.value() == 6
    assert panel.run_btn.isEnabled() and not panel.stop_btn.isEnabled()
    assert panel.status.text().startswith("Готово")


def test_metric_switch_updates_table(panel):
    sizes = [100, 200, 400, 800]
    panel.show_results([BenchmarkResult("BubbleSort", "random", n, np.array([n * n * 1e-8]), n * n / 2, 0)
                        for n in sizes])
    panel.metric_combo.setCurrentIndex(1)  # порівняння
    model, exponent, last = panel.complexity_table()["Bubble Sort"]
    assert model == "O(n²)" and exponent == pytest.approx(2.0)
    assert last == 800 * 800 / 2
    assert panel.table.item(0, 1).text() == "O(n²)"
    assert panel.table.item(0, 3).text() == "320 000"
    assert panel.table.item(0, 4).text().startswith("O(n²)")
    panel.log_check.setChecked(True)
    panel.set_theme(DARK)


def test_results_saved_to_database(app, make_db):
    from src.gui.panels.benchmark_panel import BenchmarkPanel
    db = make_db()
    SqlProgressRepository(db).create_student("Даніїл")
    runs = AlgorithmRunRepository(db)
    panel = BenchmarkPanel(runs, lambda: "Даніїл")
    saved = []
    panel.resultsSaved.connect(saved.append)
    panel.set_selected_algorithms(["Quick Sort"])
    panel.min_size.setValue(10)
    panel.max_size.setValue(20)
    panel.points.setValue(2)
    panel.repeats.setValue(1)
    run_and_wait(app, panel)
    assert saved == [2]
    assert len(runs.history(student_name="Даніїл")) == 2
    assert "Збережено в БД: 2" in panel.status.text()


def test_main_window_has_benchmark_tab(app, make_db):
    from src.gui.main_window import MainWindow
    window = MainWindow(SqlProgressRepository(make_db()))
    titles = [window.tabs.tabText(i) for i in range(window.tabs.count())]
    assert any("Порівняння" in t for t in titles)
    assert window.benchmark_panel._runs is not None
