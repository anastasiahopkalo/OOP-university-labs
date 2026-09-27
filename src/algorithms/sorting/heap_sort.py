from src.core.algorithm import SortingAlgorithm
from typing import List, TypeVar

T = TypeVar('T')

class HeapSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("HeapSort")

    def execute(self, data: List[T]) -> List[T]:
        arr = data.copy()
        self._comparisons = 0
        self._swaps = 0
        n = len(arr)

        def heapify(size: int, i: int):
            largest = i
            left = 2 * i + 1
            right = 2 * i + 2

            if left < size:
                self._comparisons += 1
                if arr[left] > arr[largest]:
                    largest = left

            if right < size:
                self._comparisons += 1
                if arr[right] > arr[largest]:
                    largest = right

            if largest != i:
                arr[i], arr[largest] = arr[largest], arr[i]
                self._swaps += 1
                self._record_step(f"Swap {arr[i]} <-> {arr[largest]}", [i, largest])
                heapify(size, largest)

        for i in range(n // 2 - 1, -1, -1):
            heapify(n, i)

        for i in range(n - 1, 0, -1):
            arr[0], arr[i] = arr[i], arr[0]
            self._swaps += 1
            self._record_step(f"Swap {arr[0]} <-> {arr[i]}", [0, i])
            heapify(i, 0)

        return arr