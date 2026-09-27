from src.core.algorithm import SortingAlgorithm
from typing import List, TypeVar

T = TypeVar('T')


class InsertionSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("InsertionSort")

    def execute(self, data: List[T]) -> List[T]:
        arr = data.copy()
        self._comparisons = 0
        self._swaps = 0
        n = len(arr)

        for i in range(1, n):
            key = arr[i]
            j = i - 1

            while j >= 0:
                self._comparisons += 1
                if arr[j] > key:
                    arr[j + 1] = arr[j]
                    self._swaps += 1
                    self._record_step(f"Shift {arr[j + 1]} to index {j + 1}", [j, j + 1])
                    j -= 1
                else:
                    break

            if j + 1 != i:
                arr[j + 1] = key
                self._swaps += 1
                self._record_step(f"Insert {key} at index {j + 1}", [j + 1])

        return arr