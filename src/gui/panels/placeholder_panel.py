from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QLabel


class PlaceholderPanel(QWidget):
    """Тимчасова вкладка для розділів, які ще в розробці."""

    def __init__(self, title: str, description: str, parent=None):
        super().__init__(parent)
        layout = QVBoxLayout(self)
        layout.addStretch()
        heading = QLabel(title)
        heading.setObjectName("title")
        heading.setAlignment(Qt.AlignCenter)
        layout.addWidget(heading)
        text = QLabel(description)
        text.setObjectName("muted")
        text.setAlignment(Qt.AlignCenter)
        text.setWordWrap(True)
        layout.addWidget(text)
        layout.addStretch()
