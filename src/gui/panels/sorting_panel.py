import random
from typing import List, Optional

from PyQt5.QtCore import Qt, QTimer, QRectF
from PyQt5.QtGui import QPainter, QFont
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox,
    QSlider, QSpinBox, QProgressBar, QLineEdit, QMessageBox, QPlainTextEdit
)

from src.core.algorithm import AlgorithmStep, SortingAlgorithm
from src.algorithms.sorting.bubble_sort import BubbleSort
from src.algorithms.sorting.insertion_sort import InsertionSort
from src.algorithms.sorting.merge_sort import MergeSort
from src.algorithms.sorting.quick_sort import QuickSort
from src.algorithms.sorting.heap_sort import HeapSort
from src.gui.step_player import StepPlayer
from src.gui.styles import Theme
from src.gui.widgets.canvas import VisualizationCanvas

ALGORITHMS = {
    "Bubble Sort": BubbleSort,
    "Insertion Sort": InsertionSort,
    "Merge Sort": MergeSort,
    "Quick Sort": QuickSort,
    "Heap Sort": HeapSort,
}

COMPLEXITY = {
    "Bubble Sort": "O(n²) · у кращому випадку O(n) · пам'ять O(1)",
    "Insertion Sort": "O(n²) · у кращому випадку O(n) · пам'ять O(1)",
    "Merge Sort": "O(n log n) завжди · пам'ять O(n)",
    "Quick Sort": "O(n log n) в середньому · O(n²) у гіршому · пам'ять O(log n)",
    "Heap Sort": "O(n log n) завжди · пам'ять O(1)",
}


class BarCanvas(VisualizationCanvas):
    """Малює масив стовпчиками й підсвічує індекси поточного кроку."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._values: List[int] = []
        self._step: Optional[AlgorithmStep] = None

    def show_values(self, values: List[int], step: Optional[AlgorithmStep] = None):
        self._values = list(values)
        self._step = step
        self.update()

    def _bar_color(self, index: int):
        step = self._step
        if step is None or index not in step.affected_indices:
            return self.color("element")
        return self.color({"compare": "compare", "done": "done"}.get(step.kind, "swap"))

    def draw(self, painter: QPainter):
        if not self._values:
            self.draw_placeholder(painter, "Немає даних")
            return

        margin = 16
        label_h = 18
        width = self.width() - 2 * margin
        height = self.height() - 2 * margin - label_h
        n = len(self._values)
        gap = 4 if n <= 40 else 1
        bar_w = max(1.0, (width - gap * (n - 1)) / n)
        low = min(0, min(self._values))
        span = (max(self._values) - low) or 1
        show_labels = bar_w >= 18

        font = QFont()
        font.setPointSize(8)
        painter.setFont(font)
        painter.setPen(Qt.NoPen)

        for i, value in enumerate(self._values):
            bar_h = max(2.0, (value - low) / span * height)
            x = margin + i * (bar_w + gap)
            y = margin + height - bar_h
            painter.setBrush(self._bar_color(i))
            painter.drawRoundedRect(QRectF(x, y, bar_w, bar_h), 3, 3)
            if show_labels:
                painter.setPen(self.color("text"))
                painter.drawText(QRectF(x, margin + height + 2, bar_w, label_h),
                                 Qt.AlignHCenter | Qt.AlignTop, str(value))
                painter.setPen(Qt.NoPen)


class SortingPanel(QWidget):
    """Вкладка з покроковою анімацією алгоритмів сортування."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._data: List[int] = []
        self._algorithm: Optional[SortingAlgorithm] = None
        self._player: StepPlayer[AlgorithmStep] = StepPlayer()
        self._timer = QTimer(self)
        self._timer.timeout.connect(self._on_tick)
        self._build_ui()
        self.randomize()

    # ---------- побудова інтерфейсу ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Візуалізація сортування")
        title.setObjectName("title")
        layout.addWidget(title)

        # Рядок 1: вибір алгоритму і даних
        data_row = QHBoxLayout()
        data_row.addWidget(QLabel("Алгоритм:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(ALGORITHMS)
        self.algo_combo.currentTextChanged.connect(self._on_algorithm_changed)
        data_row.addWidget(self.algo_combo)

        data_row.addWidget(QLabel("Розмір:"))
        self.size_spin = QSpinBox()
        self.size_spin.setRange(2, 100)
        self.size_spin.setValue(16)
        data_row.addWidget(self.size_spin)

        self.random_btn = QPushButton("🎲 Випадкові дані")
        self.random_btn.clicked.connect(self.randomize)
        data_row.addWidget(self.random_btn)

        self.custom_input = QLineEdit()
        self.custom_input.setPlaceholderText("Свої дані через кому, напр. 5, 3, 8, 1")
        self.custom_input.returnPressed.connect(self._apply_custom_data)
        data_row.addWidget(self.custom_input, stretch=1)

        apply_btn = QPushButton("Застосувати")
        apply_btn.clicked.connect(self._apply_custom_data)
        data_row.addWidget(apply_btn)
        layout.addLayout(data_row)

        self.complexity_label = QLabel()
        self.complexity_label.setObjectName("muted")
        layout.addWidget(self.complexity_label)

        # Полотно
        self.canvas = BarCanvas()
        layout.addWidget(self.canvas, stretch=1)

        # Рядок 2: керування програванням
        controls = QHBoxLayout()
        self.back_btn = QPushButton("⏮ Назад")
        self.back_btn.clicked.connect(self.step_back)
        self.play_btn = QPushButton("▶ Старт")
        self.play_btn.clicked.connect(self.toggle_play)
        self.step_btn = QPushButton("⏭ Крок")
        self.step_btn.clicked.connect(self.step_forward)
        self.reset_btn = QPushButton("🔄 Скинути")
        self.reset_btn.clicked.connect(self.reset)
        for btn in (self.back_btn, self.play_btn, self.step_btn, self.reset_btn):
            controls.addWidget(btn)

        controls.addSpacing(20)
        controls.addWidget(QLabel("Швидкість:"))
        self.speed_slider = QSlider(Qt.Horizontal)
        self.speed_slider.setRange(1, 100)
        self.speed_slider.setValue(60)
        self.speed_slider.setMaximumWidth(200)
        self.speed_slider.valueChanged.connect(self._on_speed_changed)
        controls.addWidget(self.speed_slider)
        controls.addStretch()
        layout.addLayout(controls)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.stats_label = QLabel()
        layout.addWidget(self.stats_label)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(110)
        self.log.setPlaceholderText("Тут з'являтиметься журнал кроків")
        layout.addWidget(self.log)

        self._on_algorithm_changed(self.algo_combo.currentText())

    # ---------- дані ----------

    def randomize(self):
        n = self.size_spin.value()
        self.set_data([random.randint(1, 99) for _ in range(n)])

    def _apply_custom_data(self):
        text = self.custom_input.text().replace(";", ",")
        try:
            values = [int(x) for x in text.split(",") if x.strip()]
        except ValueError:
            QMessageBox.warning(self, "Помилка", "Введіть цілі числа через кому.")
            return
        if not 2 <= len(values) <= 100:
            QMessageBox.warning(self, "Помилка", "Потрібно від 2 до 100 чисел.")
            return
        self.set_data(values)

    def set_data(self, values: List[int]):
        self._data = list(values)
        self._prepare()

    # ---------- логіка програвання ----------

    def _prepare(self):
        """Запускає алгоритм заздалегідь і завантажує його кроки в програвач."""
        self._stop()
        name = self.algo_combo.currentText()
        self._algorithm = ALGORITHMS[name]()
        self._algorithm.execute(self._data)
        self._player.load(self._algorithm.steps)
        self.log.clear()
        self._render()

    def _render(self):
        step = self._player.current
        values = step.snapshot if step else self._data
        self.canvas.show_values(values, step)
        self.progress.setValue(int(self._player.progress * 1000))

        comparisons = step.comparisons if step else 0
        swaps = step.swaps if step else 0
        action = step.action if step else "—"
        self.stats_label.setText(
            f"Крок {self._player.index + 1}/{self._player.total}   ·   "
            f"Порівнянь: {comparisons}   ·   Обмінів/записів: {swaps}   ·   {action}"
        )
        self.back_btn.setEnabled(self._player.index >= 0)
        self.step_btn.setEnabled(not self._player.finished)
        self.play_btn.setEnabled(not self._player.finished or self._timer.isActive())

    def _interval_ms(self) -> int:
        # 1 -> 1000 мс, 100 -> 5 мс
        return int(1000 * (0.995 ** (self.speed_slider.value() * 10.6)))

    def _on_speed_changed(self, _value):
        if self._timer.isActive():
            self._timer.setInterval(self._interval_ms())

    def _on_algorithm_changed(self, name: str):
        self.complexity_label.setText(f"Складність: {COMPLEXITY[name]}")
        if self._data:
            self._prepare()

    def _on_tick(self):
        self.step_forward()
        if self._player.finished:
            self._stop()

    def toggle_play(self):
        if self._timer.isActive():
            self._stop()
        else:
            if self._player.finished:
                self._player.reset()
            self._timer.start(self._interval_ms())
            self.play_btn.setText("⏸ Пауза")
            self._set_editing_enabled(False)
        self._render()

    def _stop(self):
        self._timer.stop()
        self.play_btn.setText("▶ Старт")
        self._set_editing_enabled(True)

    def _set_editing_enabled(self, enabled: bool):
        for widget in (self.algo_combo, self.size_spin, self.random_btn, self.custom_input):
            widget.setEnabled(enabled)

    def step_forward(self):
        before = self._player.index
        step = self._player.next()
        if step and self._player.index != before:
            self.log.appendPlainText(f"{self._player.index + 1:>4}. {step.action}")
        self._render()

    def step_back(self):
        self._player.previous()
        self._render()

    def reset(self):
        self._stop()
        self._player.reset()
        self.log.clear()
        self._render()

    def set_theme(self, theme: Theme):
        self.canvas.set_theme(theme)
