import pytest
from src.algorithms.sorting.quick_sort import QuickSort
from src.algorithms.sorting.bubble_sort import BubbleSort
from src.algorithms.sorting.merge_sort import MergeSort
from src.algorithms.sorting.heap_sort import HeapSort
from src.algorithms.sorting.insertion_sort import InsertionSort

ALGORITHMS = [QuickSort, BubbleSort, MergeSort, HeapSort, InsertionSort]


@pytest.mark.parametrize("algo_cls", ALGORITHMS)
class TestAlgorithmSteps:
    def test_last_step_is_sorted_snapshot(self, algo_cls):
        data = [5, 2, 9, 1, 7]
        algo = algo_cls()
        algo.execute(data)
        last = algo.steps[-1]
        assert last.kind == "done"
        assert last.snapshot == sorted(data)

    def test_steps_reset_between_runs(self, algo_cls):
        algo = algo_cls()
        algo.execute([3, 2, 1])
        first_run = len(algo.steps)
        algo.execute([3, 2, 1])
        assert len(algo.steps) == first_run

    def test_input_is_not_modified(self, algo_cls):
        data = [4, 3, 2, 1]
        algo_cls().execute(data)
        assert data == [4, 3, 2, 1]

    def test_counters_match_last_step(self, algo_cls):
        algo = algo_cls()
        algo.execute([8, 3, 5, 1])
        stats = algo.get_statistics()
        assert stats["comparisons"] == algo.steps[-1].comparisons
        assert stats["swaps"] == algo.steps[-1].swaps
        assert stats["comparisons"] > 0

    def test_step_kinds_are_known(self, algo_cls):
        algo = algo_cls()
        algo.execute([6, 1, 4, 2, 9, 3])
        assert {s.kind for s in algo.steps} <= {"compare", "swap", "set", "done"}
