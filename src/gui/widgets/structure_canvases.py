from typing import Dict, List, Optional, Tuple, Any

from PyQt5.QtCore import Qt, QPointF, QRectF
from PyQt5.QtGui import QPainter, QPen, QFont, QPolygonF

from src.gui.widgets.canvas import VisualizationCanvas

# Тип підсвічування -> назва кольору в Theme
HIGHLIGHT_COLORS = {"path": "compare", "found": "done", "new": "swap"}


class StructureCanvas(VisualizationCanvas):
    """Базове полотно для структур даних з підсвічуванням окремих елементів.

    Підсвічування задається словником {ідентифікатор елемента: тип}, де тип -
    "path" (шлях пошуку), "found" (знайдений) або "new" (щойно вставлений).
    Що саме є ідентифікатором (значення, індекс, ключ) - вирішує підклас.
    """

    def __init__(self, parent=None):
        super().__init__(parent)
        self._highlight: Dict[Any, str] = {}

    def set_highlight(self, highlight: Optional[Dict[Any, str]] = None):
        self._highlight = dict(highlight or {})
        self.update()

    def _fill_for(self, item_id: Any):
        kind = self._highlight.get(item_id)
        return self.color(HIGHLIGHT_COLORS[kind]) if kind else self.color("element")

    def _font(self, size: int = 10, bold: bool = True) -> QFont:
        font = QFont()
        font.setPointSize(size)
        font.setBold(bold)
        return font

    def _draw_arrow(self, painter: QPainter, start: QPointF, end: QPointF, head: float = 7):
        painter.setPen(QPen(self.color("muted"), 1.6))
        painter.drawLine(start, end)
        direction = end - start
        length = max((direction.x() ** 2 + direction.y() ** 2) ** 0.5, 1e-6)
        ux, uy = direction.x() / length, direction.y() / length
        left = QPointF(end.x() - head * ux + head * 0.5 * uy, end.y() - head * uy - head * 0.5 * ux)
        right = QPointF(end.x() - head * ux - head * 0.5 * uy, end.y() - head * uy + head * 0.5 * ux)
        painter.setBrush(self.color("muted"))
        painter.drawPolygon(QPolygonF([end, left, right]))


class TreeCanvas(StructureCanvas):
    """Малює бінарне дерево. Підкласи повертають вузли через _layout()."""

    RADIUS = 18

    def _layout(self) -> List[Tuple[Any, str, float, int, Optional[Any]]]:
        """Список вузлів (id, підпис, x від 0 до 1, глибина, id батька)."""
        return []

    def _tree_area(self) -> QRectF:
        return QRectF(self.rect()).adjusted(24, 30, -24, -24)

    def draw(self, painter: QPainter):
        nodes = self._layout()
        if not nodes:
            self.draw_placeholder(painter, "Структура порожня - додайте елементи")
            return
        self._draw_tree(painter, nodes, self._tree_area())

    def _draw_tree(self, painter: QPainter, nodes, area: QRectF):
        max_depth = max(depth for _, _, _, depth, _ in nodes)
        level_h = min(70.0, (area.height() - 2 * self.RADIUS) / max(max_depth, 1))
        radius = min(self.RADIUS, max(10.0, area.width() / (len(nodes) * 2.4)))

        positions = {}
        for node_id, _, x_frac, depth, _ in nodes:
            positions[node_id] = QPointF(area.left() + x_frac * area.width(),
                                         area.top() + radius + depth * level_h)

        painter.setPen(QPen(self.color("border"), 2))
        for node_id, _, _, _, parent_id in nodes:
            if parent_id is not None:
                painter.drawLine(positions[parent_id], positions[node_id])

        painter.setFont(self._font(9 if radius < 15 else 10))
        for node_id, label, _, _, _ in nodes:
            center = positions[node_id]
            painter.setPen(QPen(self.color("surface"), 2))
            painter.setBrush(self._fill_for(node_id))
            painter.drawEllipse(center, radius, radius)
            painter.setPen(Qt.white)
            painter.drawText(QRectF(center.x() - radius, center.y() - radius, 2 * radius, 2 * radius),
                             Qt.AlignCenter, label)


class BSTCanvas(TreeCanvas):
    """Бінарне дерево пошуку: x вузла - його позиція в in-order обході, id - значення."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._root = None

    def set_root(self, root):
        self._root = root
        self.update()

    def _layout(self):
        nodes = []
        order = []

        def _walk(node, depth, parent):
            if node is None:
                return
            _walk(node.left, depth + 1, node)
            order.append((node, depth, parent))
            _walk(node.right, depth + 1, node)
        _walk(self._root, 0, None)

        n = len(order)
        for i, (node, depth, parent) in enumerate(order):
            nodes.append((node.data, str(node.data), (i + 0.5) / n, depth,
                          parent.data if parent else None))
        return nodes


class HeapCanvas(TreeCanvas):
    """Купа: дерево зверху і той самий масив знизу. id вузла - індекс у масиві."""

    CELL = 34

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[Any] = []

    def set_items(self, items: List[Any]):
        self._items = list(items)
        self.update()

    def _layout(self):
        nodes = []
        for i, value in enumerate(self._items):
            depth = (i + 1).bit_length() - 1
            pos_in_level = i - (2 ** depth - 1)
            x_frac = (pos_in_level + 0.5) / 2 ** depth
            parent = (i - 1) // 2 if i > 0 else None
            nodes.append((i, str(value), x_frac, depth, parent))
        return nodes

    def _tree_area(self) -> QRectF:
        return QRectF(self.rect()).adjusted(24, 24, -24, -(self.CELL + 56))

    def draw(self, painter: QPainter):
        super().draw(painter)
        if self._items:
            self._draw_array(painter)

    def _draw_array(self, painter: QPainter):
        n = len(self._items)
        cell = min(self.CELL, (self.width() - 48) / n)
        x0 = (self.width() - cell * n) / 2
        y = self.height() - self.CELL - 32
        painter.setFont(self._font(9))
        for i, value in enumerate(self._items):
            rect = QRectF(x0 + i * cell, y, cell, self.CELL)
            painter.setPen(QPen(self.color("border"), 1))
            painter.setBrush(self._fill_for(i))
            painter.drawRect(rect)
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, str(value))
            painter.setPen(self.color("muted"))
            painter.drawText(QRectF(rect.left(), rect.bottom() + 2, cell, 20),
                             Qt.AlignHCenter | Qt.AlignTop, str(i))


class SequenceCanvas(StructureCanvas):
    """Стек, черга або зв'язний список: ряд комірок зі стрілками. id - індекс."""

    CELL_W = 56
    CELL_H = 40
    GAP = 26

    def __init__(self, parent=None):
        super().__init__(parent)
        self._items: List[Any] = []
        self._labels: Dict[int, str] = {}
        self._tail_text = ""

    def set_items(self, items: List[Any], labels: Optional[Dict[int, str]] = None, tail_text: str = ""):
        """labels - підписи над комірками (наприклад {0: "top"}), tail_text - текст після останньої."""
        self._items = list(items)
        self._labels = dict(labels or {})
        self._tail_text = tail_text
        self.update()

    def draw(self, painter: QPainter):
        if not self._items:
            self.draw_placeholder(painter, "Структура порожня - додайте елементи")
            return

        n = len(self._items)
        per_row = max(1, int((self.width() - 40 + self.GAP) // (self.CELL_W + self.GAP)))
        rows = (n + per_row - 1) // per_row
        row_h = self.CELL_H + 46
        top = max(20.0, (self.height() - rows * row_h) / 2)

        for i, value in enumerate(self._items):
            row, col = divmod(i, per_row)
            x = 20 + col * (self.CELL_W + self.GAP)
            y = top + row * row_h + 20
            rect = QRectF(x, y, self.CELL_W, self.CELL_H)

            painter.setPen(QPen(self.color("border"), 1))
            painter.setBrush(self._fill_for(i))
            painter.drawRoundedRect(rect, 5, 5)
            painter.setFont(self._font(10))
            painter.setPen(Qt.white)
            painter.drawText(rect, Qt.AlignCenter, str(value))

            if i in self._labels:
                painter.setFont(self._font(8, bold=False))
                painter.setPen(self.color("accent"))
                painter.drawText(QRectF(x, y - 18, self.CELL_W, 16), Qt.AlignCenter, self._labels[i])

            if col < per_row - 1 and i < n - 1:
                mid = y + self.CELL_H / 2
                self._draw_arrow(painter, QPointF(x + self.CELL_W + 3, mid),
                                 QPointF(x + self.CELL_W + self.GAP - 3, mid))

        if self._tail_text:
            row, col = divmod(n - 1, per_row)
            x = 20 + col * (self.CELL_W + self.GAP) + self.CELL_W + 6
            y = top + row * row_h + 20
            painter.setFont(self._font(9, bold=False))
            painter.setPen(self.color("muted"))
            painter.drawText(QRectF(x, y, 60, self.CELL_H), Qt.AlignVCenter | Qt.AlignLeft, self._tail_text)


class HashTableCanvas(StructureCanvas):
    """Хеш-таблиця: стовпчик кошиків, у кожному - ланцюжок пар. id - ключ."""

    def __init__(self, parent=None):
        super().__init__(parent)
        self._buckets: List[List[Tuple[Any, Any]]] = []

    def set_buckets(self, buckets: List[List[Tuple[Any, Any]]]):
        self._buckets = [list(b) for b in buckets]
        self.update()

    def draw(self, painter: QPainter):
        if not self._buckets:
            self.draw_placeholder(painter, "Немає кошиків")
            return

        n = len(self._buckets)
        row_h = max(16.0, min(34.0, (self.height() - 24) / n))
        cell_h = row_h - 4
        index_w = 40
        cell_w = 92
        gap = 22
        painter.setFont(self._font(8 if row_h < 24 else 9))

        for i, bucket in enumerate(self._buckets):
            y = 12 + i * row_h
            index_rect = QRectF(14, y, index_w, cell_h)
            painter.setPen(QPen(self.color("border"), 1))
            painter.setBrush(self.color("background"))
            painter.drawRect(index_rect)
            painter.setPen(self.color("muted"))
            painter.drawText(index_rect, Qt.AlignCenter, str(i))

            x = 14 + index_w
            for key, value in bucket:
                self._draw_arrow(painter, QPointF(x + 2, y + cell_h / 2), QPointF(x + gap - 2, y + cell_h / 2), 5)
                x += gap
                rect = QRectF(x, y, cell_w, cell_h)
                painter.setPen(QPen(self.color("border"), 1))
                painter.setBrush(self._fill_for(key))
                painter.drawRoundedRect(rect, 4, 4)
                painter.setPen(Qt.white)
                text = f"{key}" if value is None else f"{key}: {value}"
                painter.drawText(rect.adjusted(4, 0, -4, 0), Qt.AlignCenter,
                                 painter.fontMetrics().elidedText(text, Qt.ElideRight, int(cell_w - 8)))
                x += cell_w
