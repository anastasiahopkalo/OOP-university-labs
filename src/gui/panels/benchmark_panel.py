"""Вкладка «Порівняння»: бенчмарк алгоритмів сортування (numpy + matplotlib)."""
from typing import Callable, Dict, List, Optional

import numpy as np
from matplotlib.backends.backend_qt5agg import FigureCanvasQTAgg
from matplotlib.figure import Figure
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QFormLayout, QLabel, QPushButton, QComboBox, QSpinBox,
    QCheckBox, QListWidget, QListWidgetItem, QProgressBar, QTableWidget, QTableWidgetItem,
    QHeaderView, QSplitter, QAbstractItemView,
)

from src.core.benchmark import (
    INPUT_GENERATORS, METRICS, Benchmark, BenchmarkResult, estimate_complexity, make_sizes, series,
)
from src.database import AlgorithmRunRepository
from src.gui.panels.sorting_panel import ALGORITHMS, COMPLEXITY
from src.gui.styles import LIGHT, Theme

# Для O(n²) алгоритмів на великих n показуємо попередження про довге виконання
QUADRATIC = {"Bubble Sort", "Insertion Sort"}
# Внутрішнє ім'я алгоритму (BubbleSort) -> назва для показу (Bubble Sort)
DISPLAY_NAMES = {cls().name: title for title, cls in ALGORITHMS.items()}


def display_name(algorithm: str) -> str:
    return DISPLAY_NAMES.get(algorithm, algorithm)


class BenchmarkWorker(QThread):
    """Запускає Benchmark у фоновому потоці, щоб вікно не зависало."""

    progressed = pyqtSignal(int, int)
    finishedOk = pyqtSignal(list)
    failed = pyqtSignal(str)

    def __init__(self, benchmark: Benchmark, parent=None):
        super().__init__(parent)
        self._benchmark = benchmark
        self._stop = False

    def stop(self):
        self._stop = True

    def run(self):
        # Виняток з QThread.run() аварійно завершує PyQt5 - ловимо все
        try:
            results = self._benchmark.run(on_progress=self.progressed.emit,
                                          should_stop=lambda: self._stop)
        except Exception as error:
            self.failed.emit(str(error))
            return
        self.finishedOk.emit(results)


class BenchmarkChart(FigureCanvasQTAgg):
    """Графік метрики від розміру входу, по лінії на алгоритм."""

    def __init__(self, parent=None):
        self.figure = Figure(figsize=(7, 4), tight_layout=True)
        super().__init__(self.figure)
        self.setParent(parent)
        self._theme = LIGHT

    def set_theme(self, theme: Theme):
        self._theme = theme

    def plot(self, results: List[BenchmarkResult], metric: str, log_scale: bool):
        t = self._theme
        palette = [t.accent, t.swap, t.done, t.compare, t.element, t.muted]
        self.figure.clear()
        self.figure.set_facecolor(t.surface)
        ax = self.figure.add_subplot(1, 1, 1)
        ax.set_facecolor(t.surface)
        ax.tick_params(colors=t.muted, labelsize=8)
        for side in ("top", "right"):
            ax.spines[side].set_visible(False)
        for side in ("left", "bottom"):
            ax.spines[side].set_color(t.border)
        ax.grid(color=t.border, linewidth=0.6, alpha=0.7)
        ax.set_axisbelow(True)
        ax.set_xlabel("Розмір масиву n", color=t.muted, fontsize=9)
        ax.set_ylabel(METRICS[metric], color=t.muted, fontsize=9)

        if not results:
            ax.text(0.5, 0.5, "Запустіть порівняння", ha="center", va="center",
                    color=t.muted, transform=ax.transAxes)
            self.draw_idle()
            return

        errors = {(r.algorithm, r.size): r.std_time for r in results}
        for i, (name, (sizes, values)) in enumerate(series(results, metric).items()):
            color = palette[i % len(palette)]
            if metric == "time":
                yerr = np.array([errors[(name, n)] for n in sizes])
                ax.errorbar(sizes, values, yerr=yerr, color=color, marker="o", markersize=4,
                            linewidth=2, capsize=3, label=display_name(name))
            else:
                ax.plot(sizes, values, color=color, marker="o", markersize=4, linewidth=2,
                        label=display_name(name))
        if log_scale:
            ax.set_xscale("log")
            ax.set_yscale("log")
        legend = ax.legend(fontsize=8, frameon=False)
        for text in legend.get_texts():
            text.set_color(t.text)
        self.draw_idle()


class BenchmarkPanel(QWidget):
    """Порівнює швидкодію алгоритмів на згенерованих numpy масивах."""

    resultsSaved = pyqtSignal(int)

    def __init__(self, run_repository: Optional[AlgorithmRunRepository] = None,
                 student_name: Optional[Callable[[], str]] = None, parent=None):
        super().__init__(parent)
        self._runs = run_repository
        self._student_name = student_name
        self._worker: Optional[BenchmarkWorker] = None
        self.results: List[BenchmarkResult] = []
        self._build_ui()
        self.chart.plot([], self.current_metric, False)

    # ---------- інтерфейс ----------

    def _build_ui(self):
        controls = QWidget()
        form = QFormLayout(controls)
        title = QLabel("Порівняння алгоритмів")
        title.setObjectName("title")
        form.addRow(title)

        self.algo_list = QListWidget()
        self.algo_list.setSelectionMode(QAbstractItemView.NoSelection)
        for name in ALGORITHMS:
            item = QListWidgetItem(name)
            item.setFlags(item.flags() | Qt.ItemIsUserCheckable)
            item.setCheckState(Qt.Checked)
            item.setToolTip(COMPLEXITY[name])
            self.algo_list.addItem(item)
        self.algo_list.setFixedHeight(160)
        form.addRow(QLabel("Алгоритми"))
        form.addRow(self.algo_list)

        self.input_combo = QComboBox()
        for key, generator in INPUT_GENERATORS.items():
            self.input_combo.addItem(generator.title, key)
        form.addRow("Вхідні дані", self.input_combo)

        self.min_size = self._spin(10, 5000, 100, 50)
        self.max_size = self._spin(10, 5000, 1000, 100)
        self.points = self._spin(2, 20, 6, 1)
        self.repeats = self._spin(1, 20, 3, 1)
        form.addRow("Мінімальне n", self.min_size)
        form.addRow("Максимальне n", self.max_size)
        form.addRow("Кількість точок", self.points)
        form.addRow("Повторів", self.repeats)

        self.metric_combo = QComboBox()
        for key, title in METRICS.items():
            self.metric_combo.addItem(title, key)
        self.metric_combo.currentIndexChanged.connect(self._redraw)
        form.addRow("Метрика", self.metric_combo)

        self.log_check = QCheckBox("Логарифмічні осі")
        self.log_check.toggled.connect(self._redraw)
        form.addRow(self.log_check)

        buttons = QHBoxLayout()
        self.run_btn = QPushButton("▶ Запустити")
        self.run_btn.clicked.connect(self.start)
        self.stop_btn = QPushButton("■ Зупинити")
        self.stop_btn.setEnabled(False)
        self.stop_btn.clicked.connect(self.stop)
        buttons.addWidget(self.run_btn)
        buttons.addWidget(self.stop_btn)
        form.addRow(buttons)

        self.progress = QProgressBar()
        self.progress.setValue(0)
        form.addRow(self.progress)
        self.status = QLabel("")
        self.status.setObjectName("muted")
        self.status.setWordWrap(True)
        form.addRow(self.status)

        self.chart = BenchmarkChart()
        self.table = QTableWidget(0, 5)
        self.table.setHorizontalHeaderLabels(
            ["Алгоритм", "Оцінка", "Нахил k (v ≈ c·nᵏ)", "Значення при max n", "Теорія"])
        self.table.setEditTriggers(QAbstractItemView.NoEditTriggers)
        self.table.verticalHeader().setVisible(False)
        header = self.table.horizontalHeader()
        header.setMinimumSectionSize(60)
        header.setSectionResizeMode(QHeaderView.ResizeToContents)
        header.setStretchLastSection(True)

        right = QSplitter(Qt.Vertical)
        right.addWidget(self.chart)
        right.addWidget(self.table)
        right.setSizes([480, 200])

        layout = QHBoxLayout(self)
        controls.setMaximumWidth(300)
        layout.addWidget(controls)
        layout.addWidget(right, 1)

    @staticmethod
    def _spin(minimum: int, maximum: int, value: int, step: int) -> QSpinBox:
        spin = QSpinBox()
        spin.setRange(minimum, maximum)
        spin.setValue(value)
        spin.setSingleStep(step)
        return spin

    # ---------- параметри ----------

    @property
    def current_metric(self) -> str:
        return self.metric_combo.currentData()

    def selected_algorithms(self) -> List[str]:
        return [self.algo_list.item(i).text() for i in range(self.algo_list.count())
                if self.algo_list.item(i).checkState() == Qt.Checked]

    def set_selected_algorithms(self, names: List[str]) -> None:
        for i in range(self.algo_list.count()):
            item = self.algo_list.item(i)
            item.setCheckState(Qt.Checked if item.text() in names else Qt.Unchecked)

    def build_benchmark(self) -> Benchmark:
        names = self.selected_algorithms()
        if not names:
            raise ValueError("Виберіть хоча б один алгоритм")
        low, high = self.min_size.value(), self.max_size.value()
        if high < low:
            raise ValueError("Максимальне n менше за мінімальне")
        return Benchmark([ALGORITHMS[name] for name in names],
                         make_sizes(low, high, self.points.value()),
                         INPUT_GENERATORS[self.input_combo.currentData()],
                         repeats=self.repeats.value())

    # ---------- запуск ----------

    @property
    def running(self) -> bool:
        return self._worker is not None and self._worker.isRunning()

    def start(self):
        if self.running:
            return
        try:
            benchmark = self.build_benchmark()
        except ValueError as error:
            self.status.setText(str(error))
            return
        slow = QUADRATIC & set(self.selected_algorithms())
        hint = " Квадратичні алгоритми на великих n працюють довго." if slow and self.max_size.value() > 2000 else ""
        self.status.setText("Виконується…" + hint)
        self.progress.setRange(0, benchmark.total_runs)
        self.progress.setValue(0)
        self._set_running(True)
        self._worker = BenchmarkWorker(benchmark, self)
        self._worker.progressed.connect(lambda done, _total: self.progress.setValue(done))
        self._worker.finishedOk.connect(self._on_finished)
        self._worker.failed.connect(self._on_failed)
        self._worker.start()

    def stop(self):
        if self._worker is not None:
            self._worker.stop()

    def wait(self, msecs: int = 60000) -> bool:
        """Чекає завершення фонового потоку (для тестів і закриття вікна)."""
        return self._worker is None or self._worker.wait(msecs)

    def _set_running(self, running: bool):
        self.run_btn.setEnabled(not running)
        self.stop_btn.setEnabled(running)

    def _on_finished(self, results: List[BenchmarkResult]):
        self._set_running(False)
        self.show_results(results)
        saved = self._save(results)
        stopped = self._worker is not None and self._worker._stop
        text = "Зупинено. " if stopped else "Готово. "
        text += f"Замірів: {len(results)}."
        if saved:
            text += f" Збережено в БД: {saved}."
        self.status.setText(text)

    def _on_failed(self, message: str):
        self._set_running(False)
        self.status.setText(f"Помилка: {message}")

    def _save(self, results: List[BenchmarkResult]) -> int:
        if self._runs is None or not results:
            return 0
        try:
            student = self._student_name() if self._student_name else None
            count = self._runs.save(results, student_name=student)
        except Exception as error:  # збій БД не повинен ламати вкладку
            self.status.setText(f"Не вдалося зберегти результати: {error}")
            return 0
        self.resultsSaved.emit(count)
        return count

    # ---------- результати ----------

    def show_results(self, results: List[BenchmarkResult]):
        self.results = list(results)
        self._redraw()

    def complexity_table(self) -> Dict[str, tuple]:
        """{алгоритм: (оцінка, нахил, значення при max n)} для поточної метрики."""
        table = {}
        for name, (sizes, values) in series(self.results, self.current_metric).items():
            estimate = estimate_complexity(sizes, values)
            table[display_name(name)] = (estimate.best_model if estimate else "—",
                           estimate.exponent if estimate else None,
                           float(values[-1]) if len(values) else None)
        return table

    def _redraw(self):
        self.chart.plot(self.results, self.current_metric, self.log_check.isChecked())
        rows = self.complexity_table()
        self.table.setRowCount(len(rows))
        for row, (name, (model, exponent, last)) in enumerate(rows.items()):
            last_text = "—" if last is None else (f"{last * 1000:.2f} мс" if self.current_metric == "time" else f"{last:,.0f}".replace(",", " "))
            cells = [name, model, "—" if exponent is None else f"{exponent:.2f}", last_text,
                     COMPLEXITY.get(name, "").split(" · ")[0]]
            for col, text in enumerate(cells):
                self.table.setItem(row, col, QTableWidgetItem(text))

    def set_theme(self, theme: Theme):
        self.chart.set_theme(theme)
        self._redraw()
