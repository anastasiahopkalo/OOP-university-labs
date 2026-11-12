"""Діалог керування профілями студентів (зберігаються через ProgressRepository)."""
from typing import Callable, Optional

from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QListWidget, QListWidgetItem, QLineEdit,
    QPushButton, QMessageBox,
)

from src.database import ProgressRepository


class StudentDialog(QDialog):
    """Список студентів: вибрати, створити, видалити.

    Після accept() вибране ім'я лежить у selected_student.
    """

    def __init__(self, repository: ProgressRepository, current: str, parent=None,
                 confirm: Optional[Callable[[str], bool]] = None):
        super().__init__(parent)
        self.setWindowTitle("Студенти")
        self.setMinimumSize(380, 420)
        self._repository = repository
        self._current = current
        self._confirm = confirm or self._ask_confirmation
        self.selected_student: Optional[str] = None
        self._build_ui()
        self.reload()

    def _build_ui(self):
        layout = QVBoxLayout(self)
        layout.addWidget(QLabel("Виберіть профіль. Прогрес кожного студента зберігається окремо."))

        self.list_widget = QListWidget()
        self.list_widget.itemDoubleClicked.connect(lambda _: self.choose())
        self.list_widget.currentRowChanged.connect(lambda _: self._update_buttons())
        layout.addWidget(self.list_widget, stretch=1)

        create_row = QHBoxLayout()
        self.name_input = QLineEdit()
        self.name_input.setPlaceholderText("Ім'я нового студента")
        self.name_input.returnPressed.connect(self.create)
        self.create_btn = QPushButton("Створити")
        self.create_btn.clicked.connect(self.create)
        create_row.addWidget(self.name_input, stretch=1)
        create_row.addWidget(self.create_btn)
        layout.addLayout(create_row)

        self.error_label = QLabel()
        self.error_label.setObjectName("muted")
        self.error_label.setWordWrap(True)
        layout.addWidget(self.error_label)

        buttons = QHBoxLayout()
        self.delete_btn = QPushButton("Видалити")
        self.delete_btn.clicked.connect(self.delete_selected)
        self.choose_btn = QPushButton("Вибрати")
        self.choose_btn.setDefault(True)
        self.choose_btn.clicked.connect(self.choose)
        close_btn = QPushButton("Закрити")
        close_btn.clicked.connect(self.reject)
        buttons.addWidget(self.delete_btn)
        buttons.addStretch()
        buttons.addWidget(self.choose_btn)
        buttons.addWidget(close_btn)
        layout.addLayout(buttons)

    # ---------- дані ----------

    def students(self):
        return [self.list_widget.item(i).data(Qt.UserRole) for i in range(self.list_widget.count())]

    def reload(self, select: Optional[str] = None):
        select = select or self._current
        self.list_widget.clear()
        names = self._repository.list_students()
        if self._current not in names:
            names = sorted(names + [self._current])
        for name in names:
            item = QListWidgetItem(f"{name}   (поточний)" if name == self._current else name)
            item.setData(Qt.UserRole, name)
            self.list_widget.addItem(item)
        if select in names:
            self.list_widget.setCurrentRow(names.index(select))
        self._update_buttons()

    def current_name(self) -> Optional[str]:
        item = self.list_widget.currentItem()
        return item.data(Qt.UserRole) if item is not None else None

    def _update_buttons(self):
        name = self.current_name()
        self.choose_btn.setEnabled(name is not None)
        # поточного студента видаляти не можна - його прогрес зараз відкритий
        self.delete_btn.setEnabled(name is not None and name != self._current)

    # ---------- дії ----------

    def create(self):
        name = self.name_input.text().strip()
        try:
            self._repository.create_student(name)
        except ValueError as error:
            self.error_label.setText(str(error))
            return
        self.error_label.clear()
        self.name_input.clear()
        self.reload(select=name)

    def delete_selected(self):
        name = self.current_name()
        if name is None or name == self._current:
            return
        if not self._confirm(name):
            return
        self._repository.delete_student(name)
        self.error_label.clear()
        self.reload()

    def choose(self):
        name = self.current_name()
        if name is None:
            return
        self.selected_student = name
        self.accept()

    def _ask_confirmation(self, name: str) -> bool:
        answer = QMessageBox.question(self, "Видалити студента",
                                      f"Видалити студента «{name}» разом з усім прогресом?")
        return answer == QMessageBox.Yes
