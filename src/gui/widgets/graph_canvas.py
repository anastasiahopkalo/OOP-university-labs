import math
from typing import Any, Dict, Optional, Tuple

from PyQt5.QtCore import Qt, QPointF, QRectF, pyqtSignal
from PyQt5.QtGui import QPainter, QPen, QFont, QPolygonF

from src.core.algorithm import GraphStep
from src.data_structures.graph import Graph
from src.gui.widgets.canvas import VisualizationCanvas


class GraphCanvas(VisualizationCanvas):
    """Малює граф і стан алгоритму. Підтримує мишу:
    клік по порожньому місцю, клік по вершині, перетягування вершини.

    Позиції вершин зберігаються в частках (0..1) від розміру полотна,
    тому граф масштабується разом з вікном.
    """

    RADIUS = 20

    vertexClicked = pyqtSignal(object)
    emptyClicked = pyqtSignal(float, float)
    vertexMoved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self._graph: Optional[Graph] = None
        self._positions: Dict[Any, Tuple[float, float]] = {}
        self._step: Optional[GraphStep] = None
        self._selected = None
        self._path_edges = set()
        self._dragging = None
        self._press_pos = None
        self._moved = False
        self.setMouseTracking(False)

    # ---------- дані ----------

    def set_graph(self, graph: Graph, positions: Dict[Any, Tuple[float, float]]):
        self._graph = graph
        self._positions = positions
        self.update()

    def set_step(self, step: Optional[GraphStep]):
        self._step = step
        self.update()

    def set_selected(self, vertex):
        self._selected = vertex
        self.update()

    def set_path(self, path):
        """Підсвічує шлях (список вершин), наприклад найкоротший шлях Дейкстри."""
        self._path_edges = {frozenset(e) for e in zip(path, path[1:])}
        self.update()

    # ---------- геометрія ----------

    def _area(self) -> QRectF:
        m = self.RADIUS + 14
        return QRectF(self.rect()).adjusted(m, m, -m, -m)

    def _point(self, vertex) -> QPointF:
        fx, fy = self._positions.get(vertex, (0.5, 0.5))
        area = self._area()
        return QPointF(area.left() + fx * area.width(), area.top() + fy * area.height())

    def to_fraction(self, pos: QPointF) -> Tuple[float, float]:
        area = self._area()
        fx = (pos.x() - area.left()) / max(area.width(), 1)
        fy = (pos.y() - area.top()) / max(area.height(), 1)
        return min(max(fx, 0.0), 1.0), min(max(fy, 0.0), 1.0)

    def vertex_at(self, pos: QPointF):
        if self._graph is None:
            return None
        for vertex in reversed(self._graph.vertices()):
            p = self._point(vertex)
            if math.hypot(p.x() - pos.x(), p.y() - pos.y()) <= self.RADIUS:
                return vertex
        return None

    # ---------- миша ----------

    def mousePressEvent(self, event):
        if event.button() != Qt.LeftButton:
            return
        self._press_pos = QPointF(event.pos())
        self._dragging = self.vertex_at(self._press_pos)
        self._moved = False

    def mouseMoveEvent(self, event):
        if self._dragging is None or self._press_pos is None:
            return
        pos = QPointF(event.pos())
        if not self._moved and math.hypot(pos.x() - self._press_pos.x(), pos.y() - self._press_pos.y()) < 4:
            return
        self._moved = True
        self._positions[self._dragging] = self.to_fraction(pos)
        self.update()

    def mouseReleaseEvent(self, event):
        if event.button() != Qt.LeftButton or self._press_pos is None:
            return
        if self._moved:
            self.vertexMoved.emit()
        elif self._dragging is not None:
            self.vertexClicked.emit(self._dragging)
        else:
            self.emptyClicked.emit(*self.to_fraction(QPointF(event.pos())))
        self._dragging = None
        self._press_pos = None

    # ---------- малювання ----------

    def _vertex_color(self, vertex):
        step = self._step
        if step is not None:
            if vertex == step.current and step.kind != "done":
                return self.color("swap")
            if vertex in step.visited:
                return self.color("done")
            if vertex in step.frontier:
                return self.color("compare")
        return self.color("element")

    def _edge_style(self, u, v) -> Tuple[str, float]:
        key = frozenset((u, v))
        step = self._step
        if step is not None and step.edge and frozenset(step.edge) == key and step.kind != "done":
            return "swap", 3.5
        if key in self._path_edges:
            return "done", 4.0
        if step is not None and any(frozenset(e) == key for e in step.tree_edges):
            return "accent", 3.0
        return "border", 2.0

    def draw(self, painter: QPainter):
        if self._graph is None or self._graph.size == 0:
            self.draw_placeholder(painter, "Граф порожній.\nКлікніть на полотні, щоб додати вершину, "
                                           "або натисніть «Приклад».")
            return

        directed = self._graph.directed
        small = QFont()
        small.setPointSize(8)
        bold = QFont()
        bold.setPointSize(10)
        bold.setBold(True)

        for u, v, w in self._graph.edges():
            p1, p2 = self._point(u), self._point(v)
            color_name, width = self._edge_style(u, v)
            painter.setPen(QPen(self.color(color_name), width))
            dx, dy = p2.x() - p1.x(), p2.y() - p1.y()
            length = max(math.hypot(dx, dy), 1e-6)
            ux, uy = dx / length, dy / length
            start = QPointF(p1.x() + ux * self.RADIUS, p1.y() + uy * self.RADIUS)
            end = QPointF(p2.x() - ux * self.RADIUS, p2.y() - uy * self.RADIUS)
            painter.drawLine(start, end)
            if directed:
                head = 10
                left = QPointF(end.x() - head * ux + head * 0.5 * uy, end.y() - head * uy - head * 0.5 * ux)
                right = QPointF(end.x() - head * ux - head * 0.5 * uy, end.y() - head * uy + head * 0.5 * ux)
                painter.setBrush(self.color(color_name))
                painter.drawPolygon(QPolygonF([end, left, right]))

            mid = QPointF((p1.x() + p2.x()) / 2 - uy * 10, (p1.y() + p2.y()) / 2 + ux * 10)
            painter.setFont(small)
            painter.setPen(self.color("text"))
            label = f"{w:g}" if isinstance(w, (int, float)) else str(w)
            painter.drawText(QRectF(mid.x() - 18, mid.y() - 9, 36, 18), Qt.AlignCenter, label)

        distances = self._step.distances if self._step is not None else {}
        for vertex in self._graph.vertices():
            center = self._point(vertex)
            outline = self.color("accent") if vertex == self._selected else self.color("surface")
            painter.setPen(QPen(outline, 4 if vertex == self._selected else 2))
            painter.setBrush(self._vertex_color(vertex))
            painter.drawEllipse(center, self.RADIUS, self.RADIUS)
            painter.setFont(bold)
            painter.setPen(Qt.white)
            painter.drawText(QRectF(center.x() - self.RADIUS, center.y() - self.RADIUS,
                                    2 * self.RADIUS, 2 * self.RADIUS), Qt.AlignCenter, str(vertex))
            if vertex in distances:
                d = distances[vertex]
                painter.setFont(small)
                painter.setPen(self.color("accent"))
                text = "∞" if d == float("inf") else f"{d:g}"
                painter.drawText(QRectF(center.x() - 30, center.y() + self.RADIUS + 1, 60, 16),
                                 Qt.AlignCenter, f"d={text}")
