from src.core.algorithm import SortingAlgorithm
from typing import List, TypeVar

T = TypeVar('T')


class BubbleSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("BubbleSort")

    def execute(self, data: List[T]) -> List[T]:
        arr = data.copy()
        self._comparisons = 0
        self._swaps = 0
        n = len(arr)

        for i in range(n):
            swapped = False

            for j in range(0, n - i - 1):
                self._comparisons += 1

                if arr[j] > arr[j + 1]:
                    arr[j], arr[j + 1] = arr[j + 1], arr[j]
                    self._swaps += 1
                    swapped = True
                    self._record_step(f"Swap {arr[j]} <-> {arr[j + 1]}", [j, j + 1])

            if not swapped:
                break

        return arr