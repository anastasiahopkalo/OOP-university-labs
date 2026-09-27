from src.core.data_structure import DataStructure
from typing import TypeVar

T = TypeVar('T')


class LinkedList(DataStructure[T]):
    class Node:
        def __init__(self, data):
            self.data = data
            self.next = None

    def __init__(self):
        super().__init__("LinkedList")
        self._head = None

    def insert(self, data: T, position: int = None):
        new_node = self.Node(data)
        if position is None or position == 0:
            new_node.next = self._head
            self._head = new_node
        else:
            current = self._head
            for _ in range(position - 1):
                if current.next is None:
                    break
                current = current.next
            new_node.next = current.next
            current.next = new_node
        self._size += 1

    def delete(self, position: int) -> T:
        if self._head is None:
            return None
        if position == 0:
            data = self._head.data
            self._head = self._head.next
            self._size -= 1
            return data
        current = self._head
        for _ in range(position - 1):
            if current.next is None:
                return None
            current = current.next
        if current.next is None:
            return None
        data = current.next.data
        current.next = current.next.next
        self._size -= 1
        return data

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