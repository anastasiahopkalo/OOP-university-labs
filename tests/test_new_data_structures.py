import random
import pytest
from src.data_structures.binary_search_tree import BinarySearchTree
from src.data_structures.binary_heap import BinaryHeap
from src.data_structures.hash_table import HashTable
from src.data_structures.graph import Graph


class TestBinarySearchTree:
    @pytest.fixture
    def tree(self):
        t = BinarySearchTree()
        for v in [50, 30, 70, 20, 40, 60, 80]:
            t.insert(v)
        return t

    def test_inorder_is_sorted(self, tree):
        assert tree.get_all() == [20, 30, 40, 50, 60, 70, 80]
        assert tree.size == 7

    def test_traversals(self, tree):
        assert tree.preorder() == [50, 30, 20, 40, 70, 60, 80]
        assert tree.postorder() == [20, 40, 30, 60, 80, 70, 50]
        assert tree.level_order() == [50, 30, 70, 20, 40, 60, 80]

    def test_find_returns_depth(self, tree):
        assert tree.find(50) == 0
        assert tree.find(40) == 2
        assert tree.find(99) == -1

    def test_duplicates_ignored(self, tree):
        tree.insert(50)
        assert tree.size == 7

    def test_height_min_max(self, tree):
        assert tree.height() == 3
        assert tree.min() == 20
        assert tree.max() == 80

    @pytest.mark.parametrize("value", [20, 30, 50, 70])
    def test_remove_leaf_one_and_two_children(self, tree, value):
        assert tree.remove(value)
        expected = [v for v in [20, 30, 40, 50, 60, 70, 80] if v != value]
        assert tree.get_all() == expected
        assert tree.size == 6

    def test_remove_missing(self, tree):
        assert not tree.remove(999)

    def test_delete_by_position(self, tree):
        assert tree.delete(0) == 20
        assert tree.delete(100) is None

    def test_empty(self):
        t = BinarySearchTree()
        assert t.get_all() == [] and t.height() == 0
        assert t.min() is None and t.root is None


class TestBinaryHeap:
    def test_min_heap_pops_sorted(self):
        data = [random.randint(-50, 50) for _ in range(30)]
        heap = BinaryHeap()
        for v in data:
            heap.push(v)
        assert [heap.pop() for _ in data] == sorted(data)
        assert heap.pop() is None

    def test_max_heap(self):
        heap = BinaryHeap.heapify([3, 9, 1, 7], max_heap=True)
        assert heap.peek() == 9
        assert heap.is_max_heap

    def test_heap_property_after_delete(self):
        heap = BinaryHeap.heapify([5, 3, 8, 1, 9, 2, 7])
        heap.delete(heap.find(8))
        items = heap.get_all()
        for i in range(len(items)):
            for c in (2 * i + 1, 2 * i + 2):
                if c < len(items):
                    assert items[i] <= items[c]
        assert heap.size == 6

    def test_find_and_invalid_delete(self):
        heap = BinaryHeap.heapify([4, 2])
        assert heap.find(99) == -1
        assert heap.delete(5) is None


class TestHashTable:
    def test_put_get(self):
        table = HashTable()
        table.put("apple", 1)
        table.insert(("banana", 2))
        assert table.get("apple") == 1
        assert table.get("banana") == 2
        assert table.get("cherry", "none") == "none"

    def test_update_existing_key(self):
        table = HashTable()
        table.put("a", 1)
        table.put("a", 5)
        assert table.get("a") == 5 and table.size == 1

    def test_resize_keeps_items(self):
        table = HashTable(capacity=2)
        for i in range(50):
            table.put(i, i * i)
        assert table.capacity > 2
        assert table.load_factor <= HashTable.LOAD_FACTOR
        assert all(table.get(i) == i * i for i in range(50))

    def test_remove_and_find(self):
        table = HashTable()
        table.put("x", 1)
        assert table.find("x") >= 0
        assert table.remove("x")
        assert not table.remove("x")
        assert table.find("x") == -1 and table.size == 0

    def test_collisions_go_to_same_bucket(self):
        table = HashTable(capacity=100)
        table.put(1)
        table.put(101)
        assert table.find(1) == table.find(101)
        assert len(table.buckets()[table.find(1)]) == 2

    def test_delete_by_position(self):
        table = HashTable()
        table.put("k")
        assert table.delete(0) == "k"
        assert table.delete(0) is None


class TestGraph:
    @pytest.fixture
    def graph(self):
        g = Graph()
        g.add_edge("A", "B", 4)
        g.add_edge("A", "C", 1)
        g.add_edge("C", "B", 2)
        return g

    def test_undirected_edges(self, graph):
        assert graph.has_edge("B", "A")
        assert len(graph.edges()) == 3
        assert graph.weight("C", "A") == 1
        assert set(graph.neighbors("A")) == {"B", "C"}

    def test_directed(self):
        g = Graph(directed=True)
        g.add_edge(1, 2)
        assert g.has_edge(1, 2) and not g.has_edge(2, 1)

    def test_remove_vertex_removes_edges(self, graph):
        assert graph.remove_vertex("C")
        assert graph.size == 2
        assert graph.edges() == [("A", "B", 4)]
        assert not graph.remove_vertex("C")

    def test_remove_edge(self, graph):
        assert graph.remove_edge("A", "B")
        assert not graph.has_edge("B", "A")
        assert not graph.remove_edge("A", "Z")

    def test_base_interface(self, graph):
        graph.insert("D")
        assert graph.find("D") == 3 and graph.degree("D") == 0
        assert graph.delete(3) == "D"
        assert graph.find("D") == -1
        assert graph.get_all() == ["A", "B", "C"]
