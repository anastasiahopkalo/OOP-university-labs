from PyQt5.QtCore import QSettings
from PyQt5.QtWidgets import QMainWindow, QTabWidget, QAction, QMessageBox, QApplication

from src.gui.styles import THEMES, LIGHT, DARK, Theme, stylesheet
from src.gui.panels.sorting_panel import SortingPanel
from src.gui.panels.placeholder_panel import PlaceholderPanel

APP_NAME = "CodeLearn Studio"


class MainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle(APP_NAME)
        self.resize(1200, 800)
        self._settings = QSettings("CodeLearn", "CodeLearnStudio")

        self.tabs = QTabWidget()
        self.setCentralWidget(self.tabs)
        self._add_panels()
        self._build_menu()
        self.statusBar().showMessage("Готово")

        self._restore_settings()

    def _add_panels(self):
        self.sorting_panel = SortingPanel()
        self.tabs.addTab(self.sorting_panel, "📊 Сортування")
        # Вкладки нижче поки заглушки - їх реалізація ще в роботі
        self.tabs.addTab(PlaceholderPanel(
            "Структури даних",
            "Інтерактивна візуалізація BST, купи, хеш-таблиці, стеку та черги."),
            "🌳 Структури даних")
        self.tabs.addTab(PlaceholderPanel(
            "Графи", "Побудова графа та анімація BFS, DFS і Дейкстри."), "🕸 Графи")
        self.tabs.addTab(PlaceholderPanel(
            "Вправи", "Задачі з автоматичною перевіркою."), "💻 Вправи")
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

    def closeEvent(self, event):
        self._settings.setValue("geometry", self.saveGeometry())
        self._settings.setValue("tab", self.tabs.currentIndex())
        super().closeEvent(event)
