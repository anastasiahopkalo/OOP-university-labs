"""Тести вкладки «Вправи» і редактора коду (без дисплея)."""
import os

import pytest

os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
QtWidgets = pytest.importorskip("PyQt5.QtWidgets")

from src.core.analytics import ProgressTracker  # noqa: E402
from src.core.exercise import CodeExercise, TestCase  # noqa: E402
from src.gui.styles import DARK  # noqa: E402


@pytest.fixture(scope="module")
def app():
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def exercises():
    return [
        CodeExercise("Подвоєння", "Поверніть 2 * x", "def solve(x):\n    pass\n",
                     [TestCase((1,), 2), TestCase((5,), 10)], hint="Помножте на 2"),
        CodeExercise("Квадрат", "Поверніть x * x", "def solve(x):\n    pass\n",
                     [TestCase((3,), 9)], difficulty="Середня"),
    ]


@pytest.fixture
def panel(app, exercises):
    from src.gui.panels.exercise_panel import ExercisePanel
    return ExercisePanel(ProgressTracker("Тест"), exercises)


def run_and_wait(app, panel, code):
    panel.editor.setPlainText(code)
    panel.run_current()
    assert panel.wait_for_result()
    app.processEvents()  # сигнал з потоку доставляється через чергу подій


class TestExercisePanel:
    def test_template_loaded(self, panel):
        assert panel.task_title.text() == "Подвоєння"
        assert panel.editor.toPlainText() == "def solve(x):\n    pass\n"
        assert panel.list_widget.count() == 2

    def test_correct_solution_recorded(self, app, panel):
        recorded = []
        panel.attemptRecorded.connect(lambda title, result: recorded.append((title, result.score)))
        run_and_wait(app, panel, "def solve(x):\n    return 2 * x\n")
        assert recorded == [("Подвоєння", 100)]
        assert panel.tracker.best_score("Подвоєння") == 100
        assert panel.score_bar.value() == 100
        assert panel.table.rowCount() == 2
        assert "✅" in panel.list_widget.item(0).text()
        assert panel.run_btn.isEnabled()

    def test_wrong_solution_shows_failures(self, app, panel):
        run_and_wait(app, panel, "def solve(x):\n    return x + 1\n")
        assert panel.score_bar.value() == 50
        assert "Невірно" in panel.table.item(1, 4).text()

    def test_syntax_error_message(self, app, panel):
        run_and_wait(app, panel, "def solve(x)\n")
        assert "Помилка" in panel.result_label.text()
        assert panel.table.rowCount() == 0

    def test_drafts_kept_per_exercise(self, panel):
        panel.editor.setPlainText("# моя чернетка")
        panel.list_widget.setCurrentRow(1)
        assert panel.editor.toPlainText() == "def solve(x):\n    pass\n"
        panel.list_widget.setCurrentRow(0)
        assert panel.editor.toPlainText() == "# моя чернетка"
        panel.reset_code()
        assert panel.editor.toPlainText() == "def solve(x):\n    pass\n"

    def test_hint_toggle(self, panel):
        panel.show()
        assert not panel.hint_label.isVisible()
        panel.hint_btn.click()
        assert panel.hint_label.isVisible()
        assert "Помножте" in panel.hint_label.text()

    def test_theme_switch(self, panel):
        panel.set_theme(DARK)


class TestCodeEditor:
    def test_auto_indent_after_colon(self, app):
        from PyQt5.QtCore import Qt
        from PyQt5.QtGui import QKeyEvent
        from PyQt5.QtCore import QEvent
        from src.gui.widgets.code_editor import CodeEditor
        editor = CodeEditor()
        editor.setPlainText("def f():")
        editor.moveCursor(editor.textCursor().End)
        editor.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Return, Qt.NoModifier, "\r"))
        editor.keyPressEvent(QKeyEvent(QEvent.KeyPress, Qt.Key_Tab, Qt.NoModifier, "\t"))
        assert editor.toPlainText() == "def f():\n        "


class TestMainWindowProgress:
    def test_attempt_saved_to_file(self, app, tmp_path):
        from src.gui.main_window import MainWindow
        path = tmp_path / "progress.json"
        window = MainWindow(progress_path=path)
        panel = window.exercise_panel
        panel.list_widget.setCurrentRow(0)
        run_and_wait(app, panel, "def solve(numbers):\n    return max(numbers)\n")
        assert path.exists()
        assert ProgressTracker.load(path).best_score("Максимальний елемент") == 100
