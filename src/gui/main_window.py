from pathlib import Path
from typing import Optional

from PyQt5.QtCore import QSettings, QStandardPaths
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QMessageBox, QApplication

from src.gui.styles import THEMES, LIGHT, DARK, Theme, stylesheet
from src.gui.panels.sorting_panel import SortingPanel
from src.gui.panels.data_structures_panel import DataStructuresPanel
from src.gui.panels.graph_panel import GraphPanel
from src.gui.panels.exercise_panel import ExercisePanel
from src.core.analytics import ProgressTracker
from src.gui.panels.placeholder_panel import PlaceholderPanel

APP_NAME = "CodeLearn Studio"


def default_progress_path() -> Path:
    base = QStandardPaths.writableLocation(QStandardPaths.AppDataLocation) or str(Path.home() / ".codelearn")
    return Path(base) / "progress.json"


class MainWindow(QMainWindow):
    def __init__(self, progress_path: Optional[Path] = None):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        self._settings = QSettings("CodeLearn", "CodeLearnStudio")
        self._progress_path = Path(progress_path) if progress_path else default_progress_path()
        self.tracker = ProgressTracker.load(self._progress_path)

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._add_panels()
        self._build_menu()
        self.statusBar().showMessage("Готово")

        self._restore_settings()

    def _add_panels(self):
        self.sorting_panel = SortingPanel()
        self.tabs.addTab(self.sorting_panel, "📊 Сортування")
        self.data_structures_panel = DataStructuresPanel()
        self.tabs.addTab(self.data_structures_panel, "🌳 Структури даних")
        self.graph_panel = GraphPanel()
        self.tabs.addTab(self.graph_panel, "🕸 Графи")
        self.exercise_panel = ExercisePanel(self.tracker)
        self.exercise_panel.attemptRecorded.connect(self._on_attempt_recorded)
        self.tabs.addTab(self.exercise_panel, "💻 Вправи")
        # Вкладки нижче поки заглушки - їх реалізація ще в роботі
        self.tabs.addTab(PlaceholderPanel(
            "Прогрес", "Статистика та графіки навчання."), "📈 Прогрес")

    def _build_menu(self):
        file_menu = self.menuBar().addMenu("&Файл")
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
            "Лабораторна робота №2 з ООП.")

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
        self.statusBar().showMessage(f"{title}: {result.score}/100", 4000)

    def save_progress(self):
        try:
            self.tracker.save(self._progress_path)
        except OSError as error:
            self.statusBar().showMessage(f"Не вдалося зберегти прогрес: {error}", 5000)

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("tab", self.tabs.currentIndex())
        super().closeEvent(event)
