import pytest
from src.data_structures.linked_list import LinkedList
from src.data_structures.dynamic_array import DynamicArray
from src.data_structures.stack import Stack
from src.data_structures.queue import Queue


class TestLinkedList:
    @pytest.fixture
    def ds(self):
        return LinkedList()

    def test_works_correctly(self, ds):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        for i, val in enumerate(data):
            ds.insert(val, i)
        assert ds.get_all() == data
        assert ds.find(25) == 2

        ds.delete(2)
        assert ds.get_all() == [64, 34, 12, 22, 11, 90, 88]

    def test_empty_structure(self, ds):
        assert ds.get_all() == []
        assert ds.delete(0) is None
        assert ds.find(10) == -1

    def test_single_element(self, ds):
        ds.insert(5, 0)
        assert ds.get_all() == [5]
        assert ds.delete(0) == 5
        assert ds.get_all() == []

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, ds, data):
        for i, val in enumerate(data):
            ds.insert(val, i)
        assert ds.get_all() == data


class TestDynamicArray:
    @pytest.fixture
    def ds(self):
        return DynamicArray()

    def test_works_correctly(self, ds):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        for i, val in enumerate(data):
            ds.insert(val, i)
        assert ds.get_all() == data
        assert ds.find(25) == 2

        ds.delete(2)
        assert ds.get_all() == [64, 34, 12, 22, 11, 90, 88]

    def test_empty_structure(self, ds):
        assert ds.get_all() == []
        assert ds.delete(0) is None
        assert ds.find(10) == -1

    def test_single_element(self, ds):
        ds.insert(5, 0)
        assert ds.get_all() == [5]
        assert ds.delete(0) == 5
        assert ds.get_all() == []

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, ds, data):
        for i, val in enumerate(data):
            ds.insert(val, i)
        assert ds.get_all() == data


class TestStack:
    @pytest.fixture
    def ds(self):
        return Stack()

    def test_works_correctly(self, ds):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        for val in data:
            ds.push(val)
        # Стек повертає елементи з кінця (останній зайшов - перший вийшов)
        assert ds.get_all() == list(reversed(data))
        assert ds.peek() == 88
        assert ds.pop() == 88
        assert ds.peek() == 90

    def test_empty_structure(self, ds):
        assert ds.get_all() == []
        assert ds.pop() is None
        assert ds.peek() is None
        assert ds.find(10) == -1

    def test_single_element(self, ds):
        ds.push(5)
        assert ds.peek() == 5
        assert ds.get_all() == [5]
        assert ds.pop() == 5
        assert ds.get_all() == []

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, ds, data):
        for val in data:
            ds.push(val)
        assert ds.get_all() == list(reversed(data))


class TestQueue:
    @pytest.fixture
    def ds(self):
        return Queue()

    def test_works_correctly(self, ds):
        data = [64, 34, 25, 12, 22, 11, 90, 88]
        for val in data:
            ds.enqueue(val)
        assert ds.get_all() == data
        assert ds.peek() == 64
        assert ds.dequeue() == 64
        assert ds.peek() == 34

    def test_empty_structure(self, ds):
        assert ds.get_all() == []
        assert ds.dequeue() is None
        assert ds.peek() is None
        assert ds.find(10) == -1

    def test_single_element(self, ds):
        ds.enqueue(5)
        assert ds.peek() == 5
        assert ds.get_all() == [5]
        assert ds.dequeue() == 5
        assert ds.get_all() == []

    @pytest.mark.parametrize("data", [
        [3, 1, 2],
        [5, 4, 3, 2, 1],
        [1, 2, 3, 4, 5],
        [-5, -1, -10, 0, 5],
        [3, 3, 3, 1, 1]
    ])
    def test_various_inputs(self, ds, data):
        for val in data:
            ds.enqueue(val)
        assert ds.get_all() == data