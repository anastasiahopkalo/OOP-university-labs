from typing import List, Optional

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QLineEdit, QStackedWidget, QPlainTextEdit, QMessageBox
)

from src.gui.structure_controllers import StructureController, default_controllers, parse_value
from src.gui.styles import Theme


class DataStructuresPanel(QWidget):
    """Вкладка з інтерактивною візуалізацією структур даних."""

    def __init__(self, controllers: Optional[List[StructureController]] = None, parent=None):
        super().__init__(parent)
        self._controllers = controllers or default_controllers()
        self._build_ui()
        self._on_structure_changed(0)

    @property
    def controller(self) -> StructureController:
        return self._controllers[self.structure_combo.currentIndex()]

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Структури даних")
        title.setObjectName("title")
        layout.addWidget(title)

        row = QHBoxLayout()
        row.addWidget(QLabel("Структура:"))
        self.structure_combo = QComboBox()
        self.structure_combo.addItems([c.title for c in self._controllers])
        self.structure_combo.currentIndexChanged.connect(self._on_structure_changed)
        row.addWidget(self.structure_combo)

        self.value_input = QLineEdit()
        self.value_input.setPlaceholderText("Значення")
        self.value_input.setMaximumWidth(180)
        self.value_input.returnPressed.connect(self.insert)
        row.addWidget(self.value_input)

        self.insert_btn = QPushButton()
        self.insert_btn.clicked.connect(self.insert)
        self.delete_btn = QPushButton()
        self.delete_btn.clicked.connect(self.delete)
        self.find_btn = QPushButton("🔍 Знайти")
        self.find_btn.clicked.connect(self.find)
        self.random_btn = QPushButton("🎲 Випадково")
        self.random_btn.clicked.connect(self.fill_random)
        self.clear_btn = QPushButton("Очистити")
        self.clear_btn.clicked.connect(self.clear)
        for btn in (self.insert_btn, self.delete_btn, self.find_btn, self.random_btn, self.clear_btn):
            row.addWidget(btn)
        row.addStretch()
        layout.addLayout(row)

        self.description_label = QLabel()
        self.description_label.setObjectName("muted")
        self.description_label.setWordWrap(True)
        layout.addWidget(self.description_label)

        # Кожен контролер має власне полотно - перемикаємо їх у QStackedWidget
        self.canvas_stack = QStackedWidget()
        for controller in self._controllers:
            self.canvas_stack.addWidget(controller.canvas)
        layout.addWidget(self.canvas_stack, stretch=1)

        self.status_label = QLabel()
        layout.addWidget(self.status_label)

        self.info_label = QLabel()
        self.info_label.setObjectName("muted")
        self.info_label.setWordWrap(True)
        layout.addWidget(self.info_label)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(90)
        self.log.setPlaceholderText("Журнал операцій")
        layout.addWidget(self.log)

    def _on_structure_changed(self, index: int):
        controller = self._controllers[index]
        self.canvas_stack.setCurrentIndex(index)
        self.insert_btn.setText(controller.insert_text)
        self.delete_btn.setText(controller.delete_text)
        self.find_btn.setVisible(controller.find_supported)
        self.description_label.setText(controller.description)
        self.value_input.setPlaceholderText("Число" if controller.numeric_only else "Ключ або ключ=значення")
        self.status_label.setText("")
        self._update_info()

    def _read_value(self, required: bool = True):
        """Повертає введене значення або None, якщо поле порожнє чи некоректне."""
        text = self.value_input.text().strip()
        if not text:
            if required:
                QMessageBox.information(self, "Порожнє значення", "Спочатку введіть значення.")
            return None
        value = parse_value(text)
        if self.controller.numeric_only and not isinstance(value, int):
            QMessageBox.warning(self, "Помилка", "Ця структура працює з цілими числами.")
            return None
        return value

    def _report(self, message: str):
        self.status_label.setText(message)
        self.log.appendPlainText(f"[{self.controller.title}] {message}")
        self._update_info()

    def _update_info(self):
        self.info_label.setText(self.controller.info())

    def insert(self):
        value = self._read_value()
        if value is None:
            return
        self._report(self.controller.insert(value))
        self.value_input.clear()
        self.value_input.setFocus()

    def delete(self):
        needs_value = self.controller.delete_needs_value
        value = self._read_value(required=needs_value)
        if needs_value and value is None:
            return
        self._report(self.controller.delete(value))

    def find(self):
        value = self._read_value()
        if value is not None:
            self._report(self.controller.find(value))

    def fill_random(self):
        self.controller.fill_random()
        self._report("Заповнено випадковими значеннями")

    def clear(self):
        self.controller.clear()
        self._report("Очищено")

    def set_theme(self, theme: Theme):
        for controller in self._controllers:
            controller.canvas.set_theme(theme)
