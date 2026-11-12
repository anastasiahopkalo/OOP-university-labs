from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QSettings, QStandardPaths
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QMessageBox, QApplication

from src.gui.styles import THEMES, LIGHT, DARK, Theme, stylesheet
from src.gui.panels.sorting_panel import SortingPanel
from src.gui.panels.data_structures_panel import DataStructuresPanel
from src.gui.panels.graph_panel import GraphPanel
from src.gui.panels.exercise_panel import ExercisePanel
from src.gui.panels.dashboard_panel import DashboardPanel
from src.gui.panels.benchmark_panel import BenchmarkPanel
from src.gui.student_dialog import StudentDialog
from src.database import (
    DEFAULT_STUDENT, AlgorithmRunRepository, Database, ProgressRepository, SqlProgressRepository, migrate_json_to_sql,
)

APP_NAME = "CodeLearn Studio"


def app_data_dir() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) or str(Path.home() / ".codelearn")
    return Path(base)


def default_progress_path() -> Path:
    """JSON-файл прогресу з ЛР2 - лише для одноразового імпорту в БД."""
    return app_data_dir() / "progress.json"


def default_database_path() -> Path:
    return app_data_dir() / "codelearn.db"


def default_repository() -> SqlProgressRepository:
    """SQLite-БД у папці даних застосунку; старий progress.json переноситься в неї."""
    repository = SqlProgressRepository(Database.from_path(default_database_path()))
    migrate_json_to_sql(default_progress_path(), repository)
    return repository


class MainWindow(QMainWindow):
    def __init__(self, repository: Optional[ProgressRepository] = None,
                 student: Optional[str] = None):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        self._settings = QSettings("CodeLearn", "CodeLearnStudio")
        self.repository = repository if repository is not None else default_repository()
        self.tracker = self.repository.load(self._initial_student(student))

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._add_panels()
        self._build_menu()
        self.statusBar().showMessage("Готово")
        self._update_title()

        self._restore_settings()

    def _add_panels(self):
        self.sorting_panel = SortingPanel()
        self.tabs.addTab(self.sorting_panel, "📊 Сортування")
        runs = (AlgorithmRunRepository(self.repository.database)
                if isinstance(self.repository, SqlProgressRepository) else None)
        self.benchmark_panel = BenchmarkPanel(runs, lambda: self.student_name)
        self.tabs.addTab(self.benchmark_panel, "⏱ Порівняння")
        self.data_structures_panel = DataStructuresPanel()
        self.tabs.addTab(self.data_structures_panel, "🌳 Структури даних")
        self.graph_panel = GraphPanel()
        self.tabs.addTab(self.graph_panel, "🕸 Графи")
        self.exercise_panel = ExercisePanel(self.tracker)
        self.exercise_panel.attemptRecorded.connect(self._on_attempt_recorded)
        self.tabs.addTab(self.exercise_panel, "💻 Вправи")
        leaderboard = (self.repository.leaderboard
                       if isinstance(self.repository, SqlProgressRepository) else None)
        run_history = ((lambda: runs.history(student_name=self.student_name)) if runs is not None else None)
        self.dashboard_panel = DashboardPanel(self.tracker, self.exercise_panel.exercises, leaderboard,
                                              run_history=run_history)
        # нові заміри з вкладки «Порівняння» одразу з'являються на дашборді
        self.benchmark_panel.resultsSaved.connect(lambda _count: self.dashboard_panel.refresh())
        self.dashboard_panel.progressReset.connect(self._on_progress_reset)
        self.tabs.addTab(self.dashboard_panel, "📈 Прогрес")

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&Файл")
        student_action = QAction("Студент…", self)
        student_action.setShortcut("Ctrl+U")
        student_action.triggered.connect(self.open_student_dialog)
        file_menu.addAction(student_action)
        file_menu.addSeparator()
        quit_action = QAction("Вихід", self)
        quit_action.setShortcut("Ctrl+Q")
        quit_action.triggered.connect(self.close)
        file_menu.addAction(quit_action)

        view_menu = self.menuBar().addMenu("&Вигляд")
        self.dark_action = QAction("Темна тема", self, checkable=True)
        self.dark_action.setShortcut("Ctrl+T")
        self.dark_action.toggled.connect(
            lambda checked: self.apply_theme(DARK if checked else LIGHT))
        view_menu.addAction(self.dark_action)

        help_menu = self.menuBar().addMenu("&Довідка")
        about_action = QAction("Про програму", self)
        about_action.triggered.connect(self._show_about)
        help_menu.addAction(about_action)

    def apply_theme(self, theme: Theme):
        QApplication.instance().setStyleSheet(stylesheet(theme))
        # Кожна панель, що малює сама, отримує нову тему через set_theme()
        for i in range(self.tabs.count()):
            panel = self.tabs.widget(i)
            if hasattr(panel, "set_theme"):
                panel.set_theme(theme)
        self._settings.setValue("theme", theme.name)
        self.statusBar().showMessage(f"Тема: {theme.name}", 2000)

    def _show_about(self):
        QMessageBox.about(
            self, APP_NAME,
            f"<b>{APP_NAME}</b><br>Інтерактивне вивчення алгоритмів і структур даних.<br><br>"
            "Лабораторні роботи №1-3 з ООП.<br>"
            f"Прогрес зберігається в {self._storage_description()}.")

    def _storage_description(self) -> str:
        if isinstance(self.repository, SqlProgressRepository):
            return f"базі даних {self.repository.database.url}"
        return "JSON-файлі"

    def _restore_settings(self):
        geometry = self._settings.value("geometry")
        if geometry is not None:
            self.restoreGeometry(geometry)
        theme = THEMES.get(self._settings.value("theme", LIGHT.name), LIGHT)
        self.dark_action.setChecked(theme is DARK)
        self.apply_theme(theme)
        self.tabs.setCurrentIndex(int(self._settings.value("tab", 0)))

    def _on_attempt_recorded(self, title: str, result):
        self.save_progress()
        self.dashboard_panel.refresh()
        self.statusBar().showMessage(f"{title}: {result.score}/100", 4000)

    def _on_progress_reset(self):
        self.save_progress()
        self.exercise_panel.refresh_list()
        self.statusBar().showMessage("Прогрес скинуто", 3000)

    # ---------- студенти та прогрес ----------

    def _initial_student(self, student: Optional[str]) -> str:
        if student:
            return student
        saved = self._settings.value("student")
        if saved and self.repository.has_student(saved):
            return saved
        students = self.repository.list_students()
        return students[0] if students else DEFAULT_STUDENT

    @property
    def student_name(self) -> str:
        return self.tracker.student_name

    def switch_student(self, name: str) -> None:
        """Зберігає прогрес поточного студента і завантажує прогрес іншого."""
        if name == self.student_name:
            return
        self.save_progress()
        self.tracker = self.repository.load(name)
        self.exercise_panel.tracker = self.tracker
        self.dashboard_panel.tracker = self.tracker
        self.exercise_panel.refresh_list()
        self.dashboard_panel.refresh()
        self._settings.setValue("student", name)
        self._update_title()
        self.statusBar().showMessage(f"Студент: {name}", 3000)

    def _update_title(self):
        self.setWindowTitle(f"{APP_NAME} — {self.student_name}")

    def open_student_dialog(self) -> StudentDialog:
        """Показує діалог студентів; якщо вибрано іншого - перемикається на нього."""
        dialog = StudentDialog(self.repository, self.student_name, self)
        dialog.finished.connect(lambda _: self._on_student_dialog_closed(dialog))
        dialog.open()
        return dialog

    def _on_student_dialog_closed(self, dialog: StudentDialog):
        if dialog.selected_student:
            self.switch_student(dialog.selected_student)
        else:
            self.dashboard_panel.refresh()  # могли з'явитися або зникнути студенти в рейтингу

    def save_progress(self):
        try:
            self.repository.save(self.tracker)
        except Exception as error:  # OSError, SQLAlchemyError - GUI не повинен падати
            self.statusBar().showMessage(f"Не вдалося зберегти прогрес: {error}", 5000)

    def closeEvent(self, event):
        self.benchmark_panel.stop()
        self.benchmark_panel.wait(5000)
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("tab", self.tabs.currentIndex())
        self._settings.setValue("student", self.student_name)
        super().closeEvent(event)
