from src.core.data_structure import DataStructure
from typing import TypeVar, List, Optional

T = TypeVar('T')


class BinaryHeap(DataStructure[T]):
    """Бінарна купа на масиві. За замовчуванням min-heap, max_heap=True - max-heap."""

    def __init__(self, max_heap: bool = False):
        super().__init__("MaxHeap" if max_heap else "MinHeap")
        self._items = []
        self._max_heap = max_heap

    @property
    def is_max_heap(self) -> bool:
        return self._max_heap

    def _higher(self, a: T, b: T) -> bool:
        """True, якщо a має бути вище в купі, ніж b."""
        return a > b if self._max_heap else a < b

    def _sift_up(self, i: int):
        while i > 0:
            parent = (i - 1) // 2
            if not self._higher(self._items[i], self._items[parent]):
                break
            self._items[i], self._items[parent] = self._items[parent], self._items[i]
            i = parent

    def _sift_down(self, i: int):
        n = len(self._items)
        while True:
            best = i
            for child in (2 * i + 1, 2 * i + 2):
                if child < n and self._higher(self._items[child], self._items[best]):
                    best = child
            if best == i:
                break
            self._items[i], self._items[best] = self._items[best], self._items[i]
            i = best

    def push(self, data: T):
        self._items.append(data)
        self._size += 1
        self._sift_up(len(self._items) - 1)

    def pop(self) -> Optional[T]:
        return self.delete(0)

    def peek(self) -> Optional[T]:
        return self._items[0] if self._items else None

    def insert(self, data: T, position: int = None):
        self.push(data)

    def delete(self, position: int) -> Optional[T]:
        if not 0 <= position < len(self._items):
            return None
        last = len(self._items) - 1
        self._items[position], self._items[last] = self._items[last], self._items[position]
        data = self._items.pop()
        self._size -= 1
        if position < len(self._items):
            self._sift_down(position)
            self._sift_up(position)
        return data

    def find(self, target: T) -> int:
        for i, item in enumerate(self._items):
            if item == target:
                return i
        return -1

    def get_all(self) -> List[T]:
        """Повертає внутрішній масив купи (рівень за рівнем)."""
        return list(self._items)

    @classmethod
    def heapify(cls, data: List[T], max_heap: bool = False) -> "BinaryHeap[T]":
        heap = cls(max_heap)
        heap._items = list(data)
        heap._size = len(data)
        for i in range(len(data) // 2 - 1, -1, -1):
            heap._sift_down(i)
        return heap
