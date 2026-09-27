from src.core.data_structure import DataStructure
from typing import TypeVar

T = TypeVar('T')

class Queue(DataStructure[T]):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None

    def __init__(self):
        super().__init__("Queue")
        self._head = None
        self._tail = None

    def enqueue(self, data: T):
        new_node = self.Node(data)
        if self._tail is None:
            self._head = self._tail = new_node
        else:
            self._tail.next = new_node
            self._tail = new_node
        self._size += 1

    def dequeue(self) -> T:
        if self._head is None:
            return None
        data = self._head.data
        self._head = self._head.next
        if self._head is None:
            self._tail = None
        self._size -= 1
        return data

    def peek(self) -> T:
        if self._head is None:
            return None
        return self._head.data

    def find(self, target: T) -> int:
        current = self._head
        index = 0
        while current:
            if current.data == target:
                return index
            current = current.next
            index += 1
        return -1

    def get_all(self):
        result = []
        current = self._head
        while current:
            result.append(current.data)
            current = current.next
        return result