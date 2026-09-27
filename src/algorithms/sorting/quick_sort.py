from src.core.algorithm import SortingAlgorithm
from typing import List, TypeVar

T = TypeVar('T')


class QuickSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("QuickSort")

    def execute(self, data: List[T]) -> List[T]:
        arr = data.copy()
        self._comparisons = 0
        self._swaps = 0

        def partition(low, high):
            pivot = arr[high]
            i = low - 1
            for j in range(low, high):
                self._comparisons += 1
                if arr[j] < pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]
                    self._swaps += 1
                    self._record_step(f"Swap {arr[i]} <-> {arr[j]}", [i, j])
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            self._swaps += 1
            return i + 1

        def quicksort(low, high):
            if low < high:
                pi = partition(low, high)
                quicksort(low, pi - 1)
                quicksort(pi + 1, high)

        quicksort(0, len(arr) - 1)
        return arr