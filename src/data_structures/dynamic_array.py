from src.core.data_structure import DataStructure
from typing import TypeVar

T = TypeVar('T')


class DynamicArray(DataStructure[T]):
    def __init__(self):
        super().__init__("DynamicArray")
        self._capacity = 10
        self._array = [None] * self._capacity

    def _resize(self):
        self._capacity *= 2
        new_array = [None] * self._capacity
        for i in range(self._size):
            new_array[i] = self._array[i]
        self._array = new_array

    def insert(self, data: T, position: int = None):
        if getattr(self, '_size', 0) == self._capacity:
            self._resize()

        if position is None or position == 0:
            pos = 0
        else:
            pos = position if position < self._size else self._size

        for i in range(self._size, pos, -1):
            self._array[i] = self._array[i - 1]

        self._array[pos] = data
        self._size += 1

    def delete(self, position: int) -> T:
        if 0 <= position < self._size:
            data = self._array[position]
            for i in range(position, self._size - 1):
                self._array[i] = self._array[i + 1]
            self._array[self._size - 1] = None
            self._size -= 1
            return data
        return None

    def find(self, target: T) -> int:
        for i in range(self._size):
            if self._array[i] == target:
                return i
        return -1

    def get_all(self):
        result = []
        for i in range(self._size):
            result.append(self._array[i])
        return result