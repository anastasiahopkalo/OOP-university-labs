from typing import List, Optional, TypeVar

from src.core.data_structure import DataStructure
from src.data_structures.concurrent.atomic import AtomicReference

T = TypeVar('T')


class LockFreeStack(DataStructure[T]):
    """Стек Трайбера (Treiber, 1986) - класичний lock-free стек.

    push/pop не блокують інші потоки: кожен потік готує новий вузол і пробує
    замінити вершину одним CAS. Якщо інший потік встиг змінити вершину -
    CAS не вдається, і спроба повторюється з новим станом.
    Вузли незмінні після публікації, тому проблема ABA тут не виникає:
    Python не перевикористовує об'єкт, поки на нього є посилання.
    """

    class Node:
        __slots__ = ("data", "next")

        def __init__(self, data, next_node):
            self.data = data
            self.next = next_node

    def __init__(self):
        super().__init__("LockFreeStack")
        self._top: AtomicReference = AtomicReference(None)
        self._retries = AtomicReference(0)

    @property
    def retries(self) -> int:
        """Скільки разів CAS не вдався через конкуренцію потоків."""
        return self._retries.get()

    def _count_retry(self):
        while True:
            current = self._retries.get()
            if self._retries.compare_and_set(current, current + 1):
                return

    def push(self, data: T):
        while True:
            top = self._top.get()
            node = self.Node(data, top)
            if self._top.compare_and_set(top, node):
                return
            self._count_retry()

    def pop(self) -> Optional[T]:
        while True:
            top = self._top.get()
            if top is None:
                return None
            if self._top.compare_and_set(top, top.next):
                return top.data
            self._count_retry()

    def peek(self) -> Optional[T]:
        top = self._top.get()
        return top.data if top else None

    @property
    def size(self) -> int:
        # Лічильник розміру не ведемо: це була б ще одна спільна змінна.
        # Розмір рахуємо за знімком стеку.
        return len(self.get_all())

    def is_empty(self) -> bool:
        return self._top.get() is None

    # Реалізація абстрактних методів базового класу
    def insert(self, data: T, position: int = None):
        self.push(data)

    def delete(self, position: int = None) -> Optional[T]:
        return self.pop()

    def find(self, target: T) -> int:
        for index, value in enumerate(self.get_all()):
            if value == target:
                return index
        return -1

    def get_all(self) -> List[T]:
        """Знімок стеку від вершини. Вузли незмінні, тому обхід безпечний без блокувань."""
        result = []
        node = self._top.get()
        while node is not None:
            result.append(node.data)
            node = node.next
        return result
