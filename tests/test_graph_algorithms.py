import pytest
from src.data_structures.graph import Graph
from src.algorithms.graphs.bfs import BFS
from src.algorithms.graphs.dfs import DFS
from src.algorithms.graphs.dijkstra import Dijkstra

INF = float("inf")


@pytest.fixture
def graph():
    #   A --1-- B --2-- D
    #   |       |       |
    #   4       5       1
    #   |       |       |
    #   C --1-- E       F     G (ізольована)
    g = Graph()
    for u, v, w in [("A", "B", 1), ("A", "C", 4), ("B", "D", 2), ("B", "E", 5),
                    ("C", "E", 1), ("D", "F", 1)]:
        g.add_edge(u, v, w)
    g.add_vertex("G")
    return g


class TestBFS:
    def test_order_is_by_levels(self, graph):
        assert BFS().execute(graph, "A") == ["A", "B", "C", "D", "E", "F"]

    def test_levels_and_tree(self, graph):
        algo = BFS()
        algo.execute(graph, "A")
        last = algo.steps[-1]
        assert last.kind == "done"
        assert last.distances == {"A": 0, "B": 1, "C": 1, "D": 2, "E": 2, "F": 3}
        assert len(algo.tree_edges()) == 5

    def test_isolated_start(self, graph):
        assert BFS().execute(graph, "G") == ["G"]


class TestDFS:
    def test_order_goes_deep(self, graph):
        assert DFS().execute(graph, "A") == ["A", "B", "D", "F", "E", "C"]

    def test_stack_is_empty_at_end(self, graph):
        algo = DFS()
        algo.execute(graph, "A")
        assert algo.steps[-1].frontier == []
        assert algo.parents["C"] == "E"


class TestDijkstra:
    def test_distances(self, graph):
        result = Dijkstra().execute(graph, "A")
        assert result == {"A": 0, "B": 1, "C": 4, "D": 3, "E": 5, "F": 4, "G": INF}

    def test_path(self, graph):
        algo = Dijkstra()
        algo.execute(graph, "A")
        assert algo.path_to("F") == ["A", "B", "D", "F"]
        assert algo.path_to("E") in (["A", "C", "E"], ["A", "B", "E"])
        assert algo.path_to("G") == []

    def test_relax_steps_recorded(self, graph):
        algo = Dijkstra()
        algo.execute(graph, "A")
        kinds = {s.kind for s in algo.steps}
        assert {"visit", "relax", "done"} <= kinds
        assert algo.get_statistics()["swaps"] >= 6

    def test_negative_weight_rejected(self):
        g = Graph()
        g.add_edge(1, 2, -3)
        with pytest.raises(ValueError):
            Dijkstra().execute(g, 1)

    def test_directed(self):
        g = Graph(directed=True)
        g.add_edge("X", "Y", 2)
        assert Dijkstra().execute(g, "Y") == {"X": INF, "Y": 0}


@pytest.mark.parametrize("algo_cls", [BFS, DFS, Dijkstra])
class TestCommon:
    def test_unknown_start(self, graph, algo_cls):
        with pytest.raises(ValueError):
            algo_cls().execute(graph, "Z")

    def test_empty_graph(self, algo_cls):
        assert not algo_cls().execute(Graph())

    def test_default_start_is_first_vertex(self, graph, algo_cls):
        algo = algo_cls()
        algo.execute(graph)
        assert algo.steps[0].current == "A"

    def test_steps_reset_between_runs(self, graph, algo_cls):
        algo = algo_cls()
        algo.execute(graph, "A")
        n = len(algo.steps)
        algo.execute(graph, "A")
        assert len(algo.steps) == n


def test_dijkstra_frontier_has_no_duplicates(graph):
    algo = Dijkstra()
    algo.execute(graph, "A")
    for step in algo.steps:
        assert len(step.frontier) == len(set(step.frontier))
        assert not set(step.frontier) & set(step.visited)
