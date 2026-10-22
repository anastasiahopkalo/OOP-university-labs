from src.core.algorithm import SortingAlgorithm
from typing import List, TypeVar

T = TypeVar('T')


class MergeSort(SortingAlgorithm):
    def __init__(self):
        super().__init__("MergeSort")

    def _sort(self, arr: List[T]) -> None:
        def merge(low: int, mid: int, high: int):
            left = arr[low:mid + 1]
            right = arr[mid + 1:high + 1]

            i = 0
            j = 0
            k = low

            while i < len(left) and j < len(right):
                self._comparisons += 1
                self._record_step(f"Compare {left[i]} and {right[j]}",
                                  [low + i, mid + 1 + j], "compare")
                if left[i] <= right[j]:
                    arr[k] = left[i]
                    i += 1
                else:
                    arr[k] = right[j]
                    j += 1
                self._swaps += 1
                self._record_step(f"Assign {arr[k]} to index {k}", [k], "set")
                k += 1

            while i < len(left):
                arr[k] = left[i]
                i += 1
                self._swaps += 1
                self._record_step(f"Assign {arr[k]} to index {k}", [k], "set")
                k += 1

            while j < len(right):
                arr[k] = right[j]
                j += 1
                self._swaps += 1
                self._record_step(f"Assign {arr[k]} to index {k}", [k], "set")
                k += 1

        def merge_sort(low: int, high: int):
            if low < high:
                mid = (low + high) // 2
                merge_sort(low, mid)
                merge_sort(mid + 1, high)
                merge(low, mid, high)

        if len(arr) > 1:
            merge_sort(0, len(arr) - 1)
