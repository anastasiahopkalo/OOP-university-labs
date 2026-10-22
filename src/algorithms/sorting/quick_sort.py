from src.core.algorithm import SortingAlgorithm
from typing import List, TypeVar

T = TypeVar('T')


class QuickSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("QuickSort")

    def _sort(self, arr: List[T]) -> None:
        def partition(low, high):
            pivot = arr[high]
            i = low - 1
            for j in range(low, high):
                self._comparisons += 1
                self._record_step(f"Compare {arr[j]} with pivot {pivot}", [j, high], "compare")
                if arr[j] < pivot:
                    i += 1
                    arr[i], arr[j] = arr[j], arr[i]
                    self._swaps += 1
                    self._record_step(f"Swap {arr[i]} <-> {arr[j]}", [i, j])
            arr[i + 1], arr[high] = arr[high], arr[i + 1]
            self._swaps += 1
            self._record_step(f"Place pivot {pivot} at index {i + 1}", [i + 1, high])
            return i + 1

        def quicksort(low, high):
            if low < high:
                pi = partition(low, high)
                quicksort(low, pi - 1)
                quicksort(pi + 1, high)

        quicksort(0, len(arr) - 1)
