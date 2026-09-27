from src.core.data_structure import DataStructure
from typing import TypeVar

T = TypeVar('T')

class Stack(DataStructure[T]):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None

    def __init__(self):
        super().__init__("Stack")
        self._top = None

    def push(self, data: T):
        new_node = self.Node(data)
        new_node.next = self._top
        self._top = new_node
        self._size += 1

    def pop(self) -> T:
        if self._top is None:
            return None
        data = self._top.data
        self._top = self._top.next
        self._size -= 1
        return data

    def peek(self) -> T:
        if self._top is None:
            return None
        return self._top.data

    def find(self, target: T) -> int:
        current = self._top
        index = 0
        while current:
            if current.data == target:
                return index
            current = current.next
            index += 1
        return -1

    def get_all(self):
        result = []
        current = self._top
        while current:
            result.append(current.data)
            current = current.next
        return result