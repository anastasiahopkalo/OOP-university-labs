import math
from string import ascii_uppercase
from typing import Any, Dict, Optional, Tuple

from PyQt5.QtWidgets import (
    QWidget, QVBoxLayout, QHBoxLayout, QLabel, QPushButton, QComboBox, QCheckBox,
    QLineEdit, QDoubleSpinBox, QProgressBar, QPlainTextEdit, QTableWidget,
    QTableWidgetItem, QHeaderView, QMessageBox, QSplitter
)
from PyQt5.QtCore import Qt

from src.algorithms.graphs.bfs import BFS
from src.algorithms.graphs.dfs import DFS
from src.algorithms.graphs.dijkstra import Dijkstra
from src.core.algorithm import GraphAlgorithm, GraphStep
from src.data_structures.graph import Graph
from src.gui.step_player import StepPlayer
from src.gui.styles import Theme
from src.gui.widgets.graph_canvas import GraphCanvas
from src.gui.widgets.playback_bar import PlaybackBar

ALGORITHMS = {
    "BFS (пошук у ширину)": BFS,
    "DFS (пошук у глибину)": DFS,
    "Дейкстра (найкоротші шляхи)": Dijkstra,
}

FRONTIER_NAMES = {"BFS": "Черга", "DFS": "Стек викликів", "Dijkstra": "Пріоритетна черга"}

# Приклад графа: ребра і позиції вершин у частках полотна
EXAMPLE_EDGES = [("A", "B", 4), ("A", "C", 2), ("B", "C", 1), ("B", "D", 5), ("C", "D", 8),
                 ("C", "E", 10), ("D", "E", 2), ("D", "F", 6), ("E", "F", 3), ("E", "G", 7),
                 ("F", "G", 1)]
EXAMPLE_POSITIONS = {"A": (0.05, 0.5), "B": (0.3, 0.1), "C": (0.3, 0.9), "D": (0.55, 0.3),
                     "E": (0.55, 0.85), "F": (0.8, 0.2), "G": (0.95, 0.7)}


class GraphPanel(QWidget):
    """Вкладка для побудови графа та анімації BFS, DFS і Дейкстри."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self.graph = Graph()
        self.positions: Dict[Any, Tuple[float, float]] = {}
        self._algorithm: Optional[GraphAlgorithm] = None
        self._player: StepPlayer[GraphStep] = StepPlayer()
        self._selected = None
        self._build_ui()
        self.load_example()

    # ---------- побудова інтерфейсу ----------

    def _build_ui(self):
        layout = QVBoxLayout(self)

        title = QLabel("Графи")
        title.setObjectName("title")
        layout.addWidget(title)

        # Рядок редагування графа
        edit_row = QHBoxLayout()
        example_btn = QPushButton("Приклад")
        example_btn.clicked.connect(self.load_example)
        clear_btn = QPushButton("Очистити")
        clear_btn.clicked.connect(self.clear_graph)
        self.directed_check = QCheckBox("Орієнтований")
        self.directed_check.toggled.connect(self.set_directed)
        edit_row.addWidget(example_btn)
        edit_row.addWidget(clear_btn)
        edit_row.addWidget(self.directed_check)
        edit_row.addSpacing(16)

        edit_row.addWidget(QLabel("Ребро:"))
        self.from_input = QLineEdit()
        self.from_input.setPlaceholderText("з")
        self.from_input.setMaximumWidth(60)
        self.to_input = QLineEdit()
        self.to_input.setPlaceholderText("до")
        self.to_input.setMaximumWidth(60)
        edit_row.addWidget(self.from_input)
        edit_row.addWidget(self.to_input)
        edit_row.addWidget(QLabel("Вага:"))
        self.weight_spin = QDoubleSpinBox()
        self.weight_spin.setRange(0, 999)
        self.weight_spin.setDecimals(1)
        self.weight_spin.setValue(1)
        edit_row.addWidget(self.weight_spin)
        add_edge_btn = QPushButton("Додати ребро")
        add_edge_btn.clicked.connect(self._add_edge_from_inputs)
        edit_row.addWidget(add_edge_btn)
        self.remove_btn = QPushButton("Видалити вибрану")
        self.remove_btn.clicked.connect(self.remove_selected)
        edit_row.addWidget(self.remove_btn)
        edit_row.addStretch()
        layout.addLayout(edit_row)

        hint = QLabel("Клік на порожньому місці - нова вершина · клік на дві вершини - ребро з вагою "
                      "з поля «Вага» · перетягування - переміщення вершини")
        hint.setObjectName("muted")
        hint.setWordWrap(True)
        layout.addWidget(hint)

        # Рядок алгоритму
        algo_row = QHBoxLayout()
        algo_row.addWidget(QLabel("Алгоритм:"))
        self.algo_combo = QComboBox()
        self.algo_combo.addItems(ALGORITHMS)
        self.algo_combo.currentIndexChanged.connect(lambda _: self._prepare())
        algo_row.addWidget(self.algo_combo)
        algo_row.addWidget(QLabel("Старт:"))
        self.start_combo = QComboBox()
        self.start_combo.setMinimumWidth(60)
        self.start_combo.currentIndexChanged.connect(lambda _: self._prepare())
        algo_row.addWidget(self.start_combo)
        algo_row.addSpacing(16)
        self.playback = PlaybackBar(self._player)
        self.playback.stepChanged.connect(self._render)
        self.playback.playingChanged.connect(lambda playing: self._set_editing_enabled(not playing))
        algo_row.addWidget(self.playback, stretch=1)
        layout.addLayout(algo_row)

        # Полотно і таблиця відстаней поруч
        splitter = QSplitter(Qt.Horizontal)
        self.canvas = GraphCanvas()
        self.canvas.vertexClicked.connect(self._on_vertex_clicked)
        self.canvas.emptyClicked.connect(self._on_empty_clicked)
        splitter.addWidget(self.canvas)

        side = QWidget()
        side_layout = QVBoxLayout(side)
        side_layout.setContentsMargins(6, 0, 0, 0)
        self.table_title = QLabel()
        side_layout.addWidget(self.table_title)
        self.table = QTableWidget(0, 3)
        self.table.verticalHeader().setVisible(False)
        self.table.horizontalHeader().setSectionResizeMode(QHeaderView.Stretch)
        self.table.horizontalHeader().setMinimumSectionSize(40)
        self.table.setHorizontalScrollBarPolicy(Qt.ScrollBarAlwaysOff)
        self.table.setEditTriggers(QTableWidget.NoEditTriggers)
        side_layout.addWidget(self.table)
        side.setMinimumWidth(300)
        splitter.addWidget(side)
        splitter.setStretchFactor(0, 1)
        splitter.setStretchFactor(1, 0)
        layout.addWidget(splitter, stretch=1)

        self.progress = QProgressBar()
        self.progress.setRange(0, 1000)
        self.progress.setTextVisible(False)
        layout.addWidget(self.progress)

        self.order_label = QLabel()
        self.order_label.setWordWrap(True)
        layout.addWidget(self.order_label)
        self.frontier_label = QLabel()
        self.frontier_label.setObjectName("muted")
        layout.addWidget(self.frontier_label)

        self.log = QPlainTextEdit()
        self.log.setReadOnly(True)
        self.log.setMaximumHeight(90)
        self.log.setPlaceholderText("Журнал кроків")
        layout.addWidget(self.log)
        self.playback.stepChanged.connect(self._log_step)

    # ---------- редагування графа ----------

    def next_vertex_name(self) -> str:
        """Наступна вільна назва: A..Z, потім V27, V28..."""
        for letter in ascii_uppercase:
            if self.graph.find(letter) == -1:
                return letter
        i = 27
        while self.graph.find(f"V{i}") != -1:
            i += 1
        return f"V{i}"

    def _auto_position(self) -> Tuple[float, float]:
        """Позиція для вершини без координат - точка на колі, найвіддаленіша від інших."""
        best, best_dist = (0.5, 0.5), -1.0
        for k in range(24):
            angle = 2 * math.pi * k / 24
            candidate = (0.5 + 0.45 * math.cos(angle), 0.5 + 0.45 * math.sin(angle))
            dist = min((math.dist(candidate, p) for p in self.positions.values()), default=1.0)
            if dist > best_dist:
                best, best_dist = candidate, dist
        return best

    def add_vertex(self, name=None, position: Optional[Tuple[float, float]] = None):
        name = name if name is not None else self.next_vertex_name()
        if self.graph.find(name) == -1:
            self.graph.add_vertex(name)
            self.positions[name] = position or self._auto_position()
            self._graph_changed()
        return name

    def add_edge(self, u, v, weight: float):
        if u == v:
            return
        for vertex in (u, v):
            if self.graph.find(vertex) == -1:
                self.add_vertex(vertex)
        self.graph.add_edge(u, v, int(weight) if float(weight).is_integer() else weight)
        self._graph_changed()

    def remove_selected(self):
        if self._selected is None:
            QMessageBox.information(self, "Видалення", "Спочатку клікніть на вершину.")
            return
        self.graph.remove_vertex(self._selected)
        self.positions.pop(self._selected, None)
        self._select(None)
        self._graph_changed()

    def _add_edge_from_inputs(self):
        u, v = self.from_input.text().strip(), self.to_input.text().strip()
        if not u or not v or u == v:
            QMessageBox.warning(self, "Помилка", "Вкажіть дві різні вершини.")
            return
        self.add_edge(u, v, self.weight_spin.value())
        self.from_input.clear()
        self.to_input.clear()

    def load_example(self):
        self.graph = Graph(directed=self.directed_check.isChecked())
        self.positions = dict(EXAMPLE_POSITIONS)
        for u, v, w in EXAMPLE_EDGES:
            self.graph.add_edge(u, v, w)
        self._select(None)
        self._graph_changed()

    def clear_graph(self):
        self.graph = Graph(directed=self.directed_check.isChecked())
        self.positions = {}
        self._select(None)
        self._graph_changed()

    def set_directed(self, directed: bool):
        """Перебудовує граф з тими самими ребрами, але іншою орієнтованістю."""
        old = self.graph
        self.graph = Graph(directed=directed)
        for vertex in old.vertices():
            self.graph.add_vertex(vertex)
        for u, v, w in old.edges():
            self.graph.add_edge(u, v, w)
        self._graph_changed()

    def _graph_changed(self):
        current_start = self.start_combo.currentText()
        self.start_combo.blockSignals(True)
        self.start_combo.clear()
        self.start_combo.addItems([str(v) for v in self.graph.vertices()])
        index = self.start_combo.findText(current_start)
        self.start_combo.setCurrentIndex(max(index, 0))
        self.start_combo.blockSignals(False)
        self.canvas.set_graph(self.graph, self.positions)
        self._prepare()

    # ---------- миша ----------

    def _select(self, vertex):
        self._selected = vertex
        self.canvas.set_selected(vertex)

    def _on_empty_clicked(self, fx: float, fy: float):
        if self.playback.is_playing:
            return
        self._select(None)
        self.add_vertex(position=(fx, fy))

    def _on_vertex_clicked(self, vertex):
        if self.playback.is_playing:
            return
        if self._selected is None:
            self._select(vertex)
        elif self._selected == vertex:
            self._select(None)
        else:
            self.add_edge(self._selected, vertex, self.weight_spin.value())
            self._select(None)
        self._render()

    # ---------- алгоритм ----------

    def _prepare(self):
        """Запускає вибраний алгоритм і завантажує його кроки у програвач."""
        self.playback.stop()
        self._algorithm = ALGORITHMS[self.algo_combo.currentText()]()
        self.log.clear()
        start = self.start_combo.currentText() or None
        if start is not None and self.graph.find(start) == -1:
            start = None
        try:
            self._algorithm.execute(self.graph, start)
            self._player.load(self._algorithm.steps)
        except ValueError as error:
            self._player.load([])
            self.log.appendPlainText(f"Помилка: {error}")
        self.playback.update_buttons()
        self._render()

    def _set_editing_enabled(self, enabled: bool):
        for widget in (self.algo_combo, self.start_combo, self.directed_check, self.remove_btn):
            widget.setEnabled(enabled)

    def _render(self):
        step = self._player.current
        self.canvas.set_step(step)
        self.progress.setValue(int(self._player.progress * 1000))

        is_dijkstra = isinstance(self._algorithm, Dijkstra)
        finished = step is not None and step.kind == "done"
        if is_dijkstra and finished and self._selected is not None:
            self.canvas.set_path(self._algorithm.path_to(self._selected))
        else:
            self.canvas.set_path([])

        visited = step.visited if step else []
        name = self._algorithm.name if self._algorithm else ""
        self.order_label.setText(f"Порядок відвідування: {' → '.join(map(str, visited)) or '—'}")
        frontier = step.frontier if step else []
        self.frontier_label.setText(
            f"Крок {self._player.index + 1}/{self._player.total} · "
            f"{FRONTIER_NAMES.get(name, 'Межа')}: [{', '.join(map(str, frontier))}]"
            + (" · клікніть вершину, щоб побачити шлях до неї" if is_dijkstra and finished else ""))
        self._fill_table(step)

    def _fill_table(self, step: Optional[GraphStep]):
        is_dijkstra = isinstance(self._algorithm, Dijkstra)
        is_dfs = isinstance(self._algorithm, DFS)
        self.table_title.setText("Відстані" if is_dijkstra else ("Батьки в дереві DFS" if is_dfs else "Рівні BFS"))
        self.table.setHorizontalHeaderLabels(["Вершина", "Відстань" if is_dijkstra else
                                              ("Порядок" if is_dfs else "Рівень"), "Попередник"])
        vertices = self.graph.vertices()
        self.table.setRowCount(len(vertices))
        distances = step.distances if step else {}
        visited = step.visited if step else []
        parents = {v: p for p, v in (step.tree_edges if step else [])}
        for row, vertex in enumerate(vertices):
            if is_dfs:
                value = str(visited.index(vertex) + 1) if vertex in visited else "—"
            elif vertex in distances:
                d = distances[vertex]
                value = "∞" if d == float("inf") else f"{d:g}"
            else:
                value = "—"
            cells = [str(vertex), value, str(parents.get(vertex, "—"))]
            for col, text in enumerate(cells):
                item = QTableWidgetItem(text)
                item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(row, col, item)

    def _log_step(self):
        step = self._player.current
        if step is not None:
            self.log.appendPlainText(f"{self._player.index + 1:>4}. {step.action}")

    def set_theme(self, theme: Theme):
        self.canvas.set_theme(theme)
