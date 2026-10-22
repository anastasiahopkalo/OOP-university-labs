from typing import List, Optional, TypeVar

from src.core.data_structure import DataStructure
from src.data_structures.concurrent.atomic import AtomicReference

T = TypeVar('T')


class LockFreeQueue(DataStructure[T]):
    """Черга Майкла-Скотта (Michael & Scott, 1996) - lock-free FIFO.

    Черга завжди має фіктивний (dummy) вузол на початку. head вказує на нього,
    tail - на останній вузол. enqueue приєднує вузол CAS-ом до tail.next,
    а потім пересуває tail. Якщо потік бачить, що tail "відстав", він
    допомагає його пересунути (helping) - тому жоден потік не чекає на інший.
    """

    class Node:
        __slots__ = ("data", "next")

        def __init__(self, data=None):
            self.data = data
            self.next = AtomicReference(None)

    def __init__(self):
        super().__init__("LockFreeQueue")
        dummy = self.Node()
        self._head = AtomicReference(dummy)
        self._tail = AtomicReference(dummy)

    def enqueue(self, data: T):
        node = self.Node(data)
        while True:
            tail = self._tail.get()
            next_node = tail.next.get()
            if tail is not self._tail.get():
                continue  # tail змінився, поки ми читали - пробуємо знову
            if next_node is None:
                if tail.next.compare_and_set(None, node):
                    # Вузол опубліковано; пересунути tail - не обов'язково нам
                    self._tail.compare_and_set(tail, node)
                    return
            else:
                # tail відстав - допомагаємо іншому потоку
                self._tail.compare_and_set(tail, next_node)

    def dequeue(self) -> Optional[T]:
        while True:
            head = self._head.get()
            tail = self._tail.get()
            first = head.next.get()
            if head is not self._head.get():
                continue
            if first is None:
                return None  # черга порожня
            if head is tail:
                self._tail.compare_and_set(tail, first)
                continue
            data = first.data
            if self._head.compare_and_set(head, first):
                # first стає новим dummy-вузлом
                return data

    def peek(self) -> Optional[T]:
        first = self._head.get().next.get()
        return first.data if first else None

    @property
    def size(self) -> int:
        return len(self.get_all())

    def is_empty(self) -> bool:
        return self._head.get().next.get() is None

    # Реалізація абстрактних методів базового класу
    def insert(self, data: T, position: int = None):
        self.enqueue(data)

    def delete(self, position: int = None) -> Optional[T]:
        return self.dequeue()

    def find(self, target: T) -> int:
        for index, value in enumerate(self.get_all()):
            if value == target:
                return index
        return -1

    def get_all(self) -> List[T]:
        result = []
        node = self._head.get().next.get()
        while node is not None:
            result.append(node.data)
            node = node.next.get()
        return result
