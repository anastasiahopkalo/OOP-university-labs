from typing import Dict, List, Optional

from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QColor
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QListWidget, QListWidgetItem,
    QTableWidget, QTableWidgetItem, QHeaderView, QProgressBar, QSplitter, QMessageBox
)

from src.core.analytics import ProgressTracker
from src.core.exercise import CodeExercise, ExerciseResult
from src.core.exercise_catalog import default_exercises
from src.gui.styles import Theme
from src.gui.widgets.code_editor import CodeEditor

DIFFICULTY_COLORS = {"Легка": "#2da44e", "Середня": "#d4a017", "Складна": "#d1495b"}


class ExerciseRunner(QThread):
    """Перевіряє рішення у фоновому потоці, щоб GUI не зависав."""

    resultReady = pyqtSignal(object, object)  # (exercise, ExerciseResult)

    def __init__(self, exercise: CodeExercise, code: str, parent=None):
        super().__init__(parent)
        self._exercise = exercise
        self._code = code

    def run(self):
        # Виняток, що вилетів з QThread.run(), аварійно завершує весь застосунок PyQt5,
        # тому будь-яку помилку перетворюємо на звичайний результат
        try:
            result = self._exercise.execute(self._code)
        except Exception as error:
            result = ExerciseResult(False, 0, f"Помилка запуску перевірки: {error}", 0.0)
        self.resultReady.emit(self._exercise, result)


def _short(value, limit: int = 40) -> str:
    text = repr(value)
    return text if len(text) <= limit else text[:limit - 1] + "…"


class ExercisePanel(QWidget):
    """Вкладка з задачами та автоматичною перевіркою рішень."""

    attemptRecorded = pyqtSignal(str, object)  # (назва вправи, ExerciseResult)

    def __init__(self, tracker: Optional[ProgressTracker] = None,
                 exercises: Optional[List[CodeExercise]] = None, parent=None):
        super().__init__(parent)
        self.tracker = tracker or ProgressTracker("Студент")
        self.exercises = exercises or default_exercises()
        self._drafts: Dict[str, str] = {}
        self._runner: Optional[ExerciseRunner] = None
        self._build_ui()
        # refresh_list() вже вибрав рядок 0 без сигналу, тому завантажуємо задачу явно
        self._on_exercise_changed(0)

    @property
    def current(self) -> CodeExercise:
        return self.exercises[max(self.list_widget.currentRow(), 0)]

    def _build_ui(self):
        layout = QVBoxLayout(self)
        title = QLabel("Вправи")
        title.setObjectName("title")
        layout.addWidget(title)

        splitter = QSplitter(Qt.Horizontal)
        self.list_widget = QListWidget()
        self.list_widget.setMinimumWidth(240)
        self.list_widget.currentRowChanged.connect(self._on_exercise_changed)
        splitter.addWidget(self.list_widget)

        right = QWidget()
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(8, 0, 0, 0)
        self.task_title = QLabel()
        self.task_title.setObjectName("title")
        right_layout.addWidget(self.task_title)
        self.description = QLabel()
        self.description.setWordWrap(True)
        self.description.setTextFormat(Qt.RichText)
        right_layout.addWidget(self.description)
        self.hint_label = QLabel()
        self.hint_label.setObjectName("muted")
        self.hint_label.setWordWrap(True)
        self.hint_label.hide()
        right_layout.addWidget(self.hint_label)

        self.editor = CodeEditor()
        self.editor.textChanged.connect(self._save_draft)
        right_layout.addWidget(self.editor, stretch=3)

        buttons = QHBoxLayout()
        self.run_btn = QPushButton("▶ Перевірити")
        self.run_btn.clicked.connect(self.run_current)
        self.hint_btn = QPushButton("💡 Підказка")
        self.hint_btn.clicked.connect(lambda: self.hint_label.setVisible(not self.hint_label.isVisible()))
        self.reset_btn = QPushButton("Скинути код")
        self.reset_btn.clicked.connect(self.reset_code)
        for btn in (self.run_btn, self.hint_btn, self.reset_btn):
            buttons.addWidget(btn)
        buttons.addStretch()
        self.result_label = QLabel()
        buttons.addWidget(self.result_label)
        self.score_bar = QProgressBar()
        self.score_bar.setRange(0, 100)
        self.score_bar.setMaximumWidth(160)
        self.score_bar.setFormat("%v / 100")
        buttons.addWidget(self.score_bar)
        right_layout.addLayout(buttons)

        self.table = QTableWidget(0, 6)
        self.table.setHorizontalHeaderLabels(["#", "Вхідні дані", "Очікується", "Отримано", "Статус", "Час"])
        self.table.verticalHeader().setVisible(False)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(30)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        for col in (1, 2, 3):
            header.setSectionResizeMode(col, QHeaderView.Stretch)
        header.setSectionResizeMode(0, QHeaderView.Fixed)
        header.resizeSection(0, 36)
        right_layout.addWidget(self.table, stretch=2)

        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        layout.addWidget(splitter, stretch=1)
        self.refresh_list()

    # ---------- список задач ----------

    def refresh_list(self):
        row = self.list_widget.currentRow()
        self.list_widget.blockSignals(True)
        self.list_widget.clear()
        for exercise in self.exercises:
            best = self.tracker.best_score(exercise.title)
            mark = "✅" if best == 100 else ("◐" if best else "○")
            item = QListWidgetItem(f"{mark}  {exercise.title}\n      {exercise.difficulty}"
                                   + (f" · найкраще {best}/100" if best is not None else ""))
            item.setForeground(QColor(DIFFICULTY_COLORS.get(exercise.difficulty, "#888888")))
            self.list_widget.addItem(item)
        self.list_widget.setCurrentRow(max(row, 0))
        self.list_widget.blockSignals(False)

    def _on_exercise_changed(self, row: int):
        if row < 0:
            return
        exercise = self.exercises[row]
        self.task_title.setText(exercise.title)
        self.description.setText(exercise.description)
        self.hint_label.setText(f"Підказка: {exercise.hint}")
        self.hint_label.hide()
        self.hint_btn.setEnabled(bool(exercise.hint))
        self.editor.blockSignals(True)
        self.editor.setPlainText(self._drafts.get(exercise.title, exercise.template))
        self.editor.blockSignals(False)
        self.table.setRowCount(0)
        self.result_label.setText("")
        self.score_bar.setValue(0)

    def _save_draft(self):
        self._drafts[self.current.title] = self.editor.toPlainText()

    def reset_code(self):
        self._drafts.pop(self.current.title, None)
        self.editor.setPlainText(self.current.template)

    # ---------- перевірка ----------

    def run_current(self):
        if self._runner is not None and self._runner.isRunning():
            return
        code = self.editor.toPlainText()
        if not code.strip():
            QMessageBox.information(self, "Порожній код", "Спочатку напишіть рішення.")
            return
        self.run_btn.setEnabled(False)
        self.run_btn.setText("⏳ Перевіряю...")
        self._runner = ExerciseRunner(self.current, code, self)
        self._runner.resultReady.connect(self._on_result)
        self._runner.start()

    def wait_for_result(self, timeout_ms: int = 15000) -> bool:
        """Для тестів: чекає завершення перевірки."""
        return self._runner.wait(timeout_ms) if self._runner else True

    def _on_result(self, exercise: CodeExercise, result: ExerciseResult):
        self.run_btn.setEnabled(True)
        self.run_btn.setText("▶ Перевірити")
        self.tracker.record_attempt(exercise.title, result)
        self.attemptRecorded.emit(exercise.title, result)
        self.refresh_list()
        if exercise is self.current:
            self.show_result(result)

    def show_result(self, result: ExerciseResult):
        self.result_label.setText(result.message)
        self.score_bar.setValue(result.score)
        self.table.setRowCount(len(result.details))
        status_text = {"ok": "", "error": "помилка", "timeout": "тайм-аут"}
        for row, detail in enumerate(result.details):
            args = detail.args[0] if len(detail.args) == 1 else detail.args
            status = "✓ Пройдено" if detail.passed else "✗ " + (status_text[detail.status] or "Невірно")
            cells = [str(row + 1), _short(args), _short(detail.expected),
                     _short(detail.actual) if detail.status == "ok" else str(detail.actual),
                     status, f"{detail.elapsed * 1000:.2f} мс"]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                if col == 4:
                    item.setForeground(QColor("#2da44e" if detail.passed else "#d1495b"))
                self.table.setItem(row, col, item)

    def set_theme(self, theme: Theme):
        self.editor.set_theme(theme)
