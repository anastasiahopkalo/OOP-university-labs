import random
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from src.core.data_structure import DataStructure
from src.data_structures.binary_search_tree import BinarySearchTree
from src.data_structures.binary_heap import BinaryHeap
from src.data_structures.hash_table import HashTable
from src.data_structures.stack import Stack
from src.data_structures.queue import Queue
from src.data_structures.linked_list import LinkedList
from src.gui.widgets.structure_canvases import (
    StructureCanvas, BSTCanvas, HeapCanvas, SequenceCanvas, HashTableCanvas
)


def parse_value(text: str) -> Any:
    """Перетворює введений текст на int, якщо це можливо, інакше лишає рядком."""
    text = text.strip()
    try:
        return int(text)
    except ValueError:
        return text


class StructureController(ABC):
    """Зв'язує структуру даних з її полотном і операціями в GUI.

    Панель працює з усіма структурами однаково через цей інтерфейс,
    а кожен підклас знає особливості своєї структури (поліморфізм).
    """

    title = ""
    description = ""
    insert_text = "Вставити"
    delete_text = "Видалити"
    delete_needs_value = True
    find_supported = True
    numeric_only = True

    def __init__(self):
        self.structure: DataStructure = self._create()
        self.canvas: StructureCanvas = self._create_canvas()
        self.refresh()

    @abstractmethod
    def _create(self) -> DataStructure:
        pass

    @abstractmethod
    def _create_canvas(self) -> StructureCanvas:
        pass

    @abstractmethod
    def refresh(self, highlight: Optional[Dict[Any, str]] = None):
        """Передає полотну поточний стан структури."""
        pass

    @abstractmethod
    def insert(self, value: Any) -> str:
        pass

    @abstractmethod
    def delete(self, value: Any) -> str:
        pass

    def find(self, value: Any) -> str:
        index = self.structure.find(value)
        if index == -1:
            self.refresh()
            return f"{value} не знайдено"
        self.refresh({index: "found"})
        return f"{value} знайдено на позиції {index}"

    def clear(self):
        self.structure = self._create()
        self.refresh()

    def info(self) -> str:
        return f"Розмір: {self.structure.size}"

    def random_value(self) -> Any:
        return random.randint(1, 99)

    def fill_random(self, count: int = 7):
        self.clear()
        for _ in range(count):
            self.insert(self.random_value())
        self.refresh()


class BSTController(StructureController):
    title = "Бінарне дерево пошуку"
    description = ("Ліве піддерево менше за вузол, праве - більше. "
                   "Пошук, вставка й видалення - O(h), де h - висота дерева.")

    def _create(self):
        return BinarySearchTree()

    def _create_canvas(self):
        return BSTCanvas()

    def refresh(self, highlight=None):
        self.canvas.set_root(self.structure.root)
        self.canvas.set_highlight(highlight)

    def _search_path(self, value):
        path = []
        node = self.structure.root
        while node is not None:
            path.append(node.data)
            if value == node.data:
                break
            node = node.left if value < node.data else node.right
        return path

    def insert(self, value):
        if self.structure.contains(value):
            self.refresh({value: "found"})
            return f"{value} вже є в дереві - дублікати не зберігаються"
        self.structure.insert(value)
        highlight = {v: "path" for v in self._search_path(value)}
        highlight[value] = "new"
        self.refresh(highlight)
        return f"Вставлено {value} на глибину {self.structure.find(value)}"

    def delete(self, value):
        if not self.structure.remove(value):
            self.refresh()
            return f"{value} немає в дереві"
        self.refresh()
        return f"Видалено {value}"

    def find(self, value):
        path = self._search_path(value)
        highlight = {v: "path" for v in path}
        found = bool(path) and path[-1] == value
        if found:
            highlight[value] = "found"
        self.refresh(highlight)
        route = " → ".join(map(str, path)) or "—"
        return f"{'Знайдено' if found else 'Не знайдено'} {value}. Шлях: {route} ({len(path)} порівнянь)"

    def info(self):
        bst = self.structure
        if bst.size == 0:
            return "Розмір: 0"
        return (f"Розмір: {bst.size} · Висота: {bst.height()} · Мін: {bst.min()} · Макс: {bst.max()}\n"
                f"Preorder: {bst.preorder()}\nInorder: {bst.inorder()}")


class HeapController(StructureController):
    delete_needs_value = False

    def __init__(self, max_heap: bool = False):
        self._max_heap = max_heap
        self.title = "Max-купа" if max_heap else "Min-купа"
        self.description = (f"Повне бінарне дерево у масиві: батько {'≥' if max_heap else '≤'} нащадків. "
                            f"Нащадки i-го вузла - 2i+1 і 2i+2. push і pop - O(log n).")
        self.delete_text = "Видобути max" if max_heap else "Видобути min"
        super().__init__()

    def _create(self):
        return BinaryHeap(max_heap=self._max_heap)

    def _create_canvas(self):
        return HeapCanvas()

    def refresh(self, highlight=None):
        self.canvas.set_items(self.structure.get_all())
        self.canvas.set_highlight(highlight)

    def insert(self, value):
        self.structure.push(value)
        index = self.structure.find(value)
        self.refresh({index: "new"})
        return f"Вставлено {value}, після просіювання вгору він на позиції {index}"

    def delete(self, value=None):
        top = self.structure.pop()
        self.refresh({0: "found"} if self.structure.size else None)
        return "Купа порожня" if top is None else f"Видобуто {top}"

    def info(self):
        heap = self.structure
        return f"Розмір: {heap.size} · Вершина: {heap.peek() if heap.size else '—'}"


class HashTableController(StructureController):
    title = "Хеш-таблиця"
    description = ("Ключ потрапляє в кошик hash(key) % capacity. Колізії - ланцюжки. "
                   "Якщо load factor > 0.75, таблиця подвоюється. Введіть ключ або ключ=значення.")
    numeric_only = False

    def _create(self):
        return HashTable(capacity=8)

    def _create_canvas(self):
        return HashTableCanvas()

    def refresh(self, highlight=None):
        self.canvas.set_buckets(self.structure.buckets())
        self.canvas.set_highlight(highlight)

    @staticmethod
    def _split(value):
        if isinstance(value, str) and "=" in value:
            key, val = value.split("=", 1)
            return parse_value(key), parse_value(val)
        return value, None

    def insert(self, value):
        key, val = self._split(value)
        capacity_before = self.structure.capacity
        self.structure.put(key, val)
        self.refresh({key: "new"})
        message = f"Ключ {key!r} у кошику {self.structure.find(key)}"
        if self.structure.capacity != capacity_before:
            message += f" · таблицю розширено до {self.structure.capacity} кошиків"
        return message

    def delete(self, value):
        key, _ = self._split(value)
        removed = self.structure.remove(key)
        self.refresh()
        return f"Видалено ключ {key!r}" if removed else f"Ключа {key!r} немає"

    def find(self, value):
        key, _ = self._split(value)
        bucket = self.structure.find(key)
        if bucket == -1:
            self.refresh()
            return f"Ключа {key!r} немає"
        self.refresh({key: "found"})
        return f"Ключ {key!r} у кошику {bucket}, значення: {self.structure.get(key)!r}"

    def random_value(self):
        word = random.choice(["apple", "kiwi", "mango", "lime", "plum", "pear", "fig", "date",
                              "cat", "dog", "owl", "fox", "bee", "elk"])
        return f"{word}={random.randint(1, 99)}"

    def info(self):
        table = self.structure
        longest = max((len(b) for b in table.buckets()), default=0)
        return (f"Розмір: {table.size} · Кошиків: {table.capacity} · "
                f"Load factor: {table.load_factor:.2f} · Найдовший ланцюжок: {longest}")


class StackController(StructureController):
    title = "Стек (LIFO)"
    description = "Останній прийшов - перший вийшов. push, pop і peek - O(1)."
    insert_text = "Push"
    delete_text = "Pop"
    delete_needs_value = False

    def _create(self):
        return Stack()

    def _create_canvas(self):
        return SequenceCanvas()

    def refresh(self, highlight=None):
        self.canvas.set_items(self.structure.get_all(), {0: "top"})
        self.canvas.set_highlight(highlight)

    def insert(self, value):
        self.structure.push(value)
        self.refresh({0: "new"})
        return f"Push {value}"

    def delete(self, value=None):
        top = self.structure.pop()
        self.refresh()
        return "Стек порожній" if top is None else f"Pop → {top}"


class QueueController(StructureController):
    title = "Черга (FIFO)"
    description = "Перший прийшов - перший вийшов. enqueue і dequeue - O(1)."
    insert_text = "Enqueue"
    delete_text = "Dequeue"
    delete_needs_value = False

    def _create(self):
        return Queue()

    def _create_canvas(self):
        return SequenceCanvas()

    def refresh(self, highlight=None):
        items = self.structure.get_all()
        labels = {0: "head"}
        if items:
            labels[len(items) - 1] = "head / tail" if len(items) == 1 else "tail"
        self.canvas.set_items(items, labels)
        self.canvas.set_highlight(highlight)

    def insert(self, value):
        self.structure.enqueue(value)
        self.refresh({self.structure.size - 1: "new"})
        return f"Enqueue {value}"

    def delete(self, value=None):
        front = self.structure.dequeue()
        self.refresh()
        return "Черга порожня" if front is None else f"Dequeue → {front}"


class LinkedListController(StructureController):
    title = "Однозв'язний список"
    description = ("Кожен вузол зберігає значення і посилання на наступний. "
                   "Вставка в кінець і пошук - O(n), вставка на початок - O(1).")
    insert_text = "Додати в кінець"

    def _create(self):
        return LinkedList()

    def _create_canvas(self):
        return SequenceCanvas()

    def refresh(self, highlight=None):
        self.canvas.set_items(self.structure.get_all(), {0: "head"}, "→ None")
        self.canvas.set_highlight(highlight)

    def insert(self, value):
        self.structure.insert(value, self.structure.size)
        self.refresh({self.structure.size - 1: "new"})
        return f"Додано {value} в кінець"

    def delete(self, value):
        index = self.structure.find(value)
        if index == -1:
            self.refresh()
            return f"{value} немає в списку"
        self.structure.delete(index)
        self.refresh()
        return f"Видалено {value} з позиції {index}"


def default_controllers():
    return [
        BSTController(),
        HeapController(max_heap=False),
        HeapController(max_heap=True),
        HashTableController(),
        StackController(),
        QueueController(),
        LinkedListController(),
    ]
