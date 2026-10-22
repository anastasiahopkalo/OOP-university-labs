from abc import abstractmethod

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QPainter, QColor
from PyQt5.QtWidgets import QWidget, QSizePolicy

from src.gui.styles import Theme, LIGHT


class VisualizationCanvas(QWidget):
    """Базове полотно для всіх візуалізацій.

    Відповідає за тему, фон і згладжування. Підкласи (стовпчики масиву,
    дерево, граф, хеш-таблиця...) реалізують лише draw().
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._theme = LIGHT
        self.setMinimumHeight(260)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)

    @property
    def theme(self) -> Theme:
        return self._theme

    def set_theme(self, theme: Theme):
        self._theme = theme
        self.update()

    def color(self, name: str) -> QColor:
        """Колір з поточної теми за назвою поля, наприклад color("swap")."""
        return QColor(getattr(self._theme, name))

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.Antialiasing)
        painter.fillRect(self.rect(), self.color("surface"))
        self.draw(painter)
        painter.end()

    @abstractmethod
    def draw(self, painter: QPainter):
        pass

    def draw_placeholder(self, painter: QPainter, text: str):
        painter.setPen(self.color("muted"))
        painter.drawText(self.rect(), Qt.AlignCenter, text)
