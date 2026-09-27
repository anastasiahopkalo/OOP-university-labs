import pytest
from src.algorithms.sorting.quick_sort import QuickSort
from src.algorithms.sorting.bubble_sort import BubbleSort
from src.algorithms.sorting.merge_sort import MergeSort
from src.algorithms.sorting.heap_sort import HeapSort
from src.algorithms.sorting.insertion_sort import InsertionSort


class TestQuickSort:
    @pytest.fixture
    def algo(self):
        return QuickSort()

    def test_sorts_correctly(self, algo):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        result = algo.execute(data)
        assert result == sorted(data)

    def test_empty_list(self, algo):
        assert algo.execute([]) == []

    def test_single_element(self, algo):
        assert algo.execute([5]) == [5]

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, algo, data):
        assert algo.execute(data) == sorted(data)


class TestBubbleSort:
    @pytest.fixture
    def algo(self):
        return BubbleSort()

    def test_sorts_correctly(self, algo):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        result = algo.execute(data)
        assert result == sorted(data)

    def test_empty_list(self, algo):
        assert algo.execute([]) == []

    def test_single_element(self, algo):
        assert algo.execute([5]) == [5]

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, algo, data):
        assert algo.execute(data) == sorted(data)


class TestMergeSort:
    @pytest.fixture
    def algo(self):
        return MergeSort()

    def test_sorts_correctly(self, algo):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        result = algo.execute(data)
        assert result == sorted(data)

    def test_empty_list(self, algo):
        assert algo.execute([]) == []

    def test_single_element(self, algo):
        assert algo.execute([5]) == [5]

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, algo, data):
        assert algo.execute(data) == sorted(data)


class TestHeapSort:
    @pytest.fixture
    def algo(self):
        return HeapSort()

    def test_sorts_correctly(self, algo):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        result = algo.execute(data)
        assert result == sorted(data)

    def test_empty_list(self, algo):
        assert algo.execute([]) == []

    def test_single_element(self, algo):
        assert algo.execute([5]) == [5]

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, algo, data):
        assert algo.execute(data) == sorted(data)


class TestInsertionSort:
    @pytest.fixture
    def algo(self):
        return InsertionSort()

    def test_sorts_correctly(self, algo):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        result = algo.execute(data)
        assert result == sorted(data)

    def test_empty_list(self, algo):
        assert algo.execute([]) == []

    def test_single_element(self, algo):
        assert algo.execute([5]) == [5]

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, algo, data):
        assert algo.execute(data) == sorted(data)