"""networkx: конвертація графів, розкладки, генератори, метрики
і звірка наших BFS / DFS / Dijkstra з еталонними реалізаціями networkx."""
import networkx as nx
import pytest

from src.algorithms.graphs.bfs import BFS
from src.algorithms.graphs.dfs import DFS
from src.algorithms.graphs.dijkstra import Dijkstra
from src.algorithms.graphs.nx_adapter import (
    GENERATORS, LAYOUTS, CompleteGenerator, GridGenerator, RandomGraphGenerator, TreeGenerator,
    compute_layout, from_networkx, graph_metrics, normalize_positions, spread_positions, to_networkx,
    vertex_names,
)
from src.data_structures.graph import Graph

SEEDS = range(30)


def sample(directed=False):
    g = Graph(directed=directed)
    for u, v, w in [("A", "B", 4), ("B", "C", 1), ("A", "C", 7)]:
        g.add_edge(u, v, w)
    g.add_vertex("D")
    return g


class TestConversion:
    @pytest.mark.parametrize("directed", [False, True])
    def test_round_trip(self, directed):
        g = sample(directed)
        nx_graph = to_networkx(g)
        assert nx_graph.is_directed() == directed
        assert set(nx_graph.nodes) == {"A", "B", "C", "D"}
        assert nx_graph.edges["A", "B"]["weight"] == 4
        back = from_networkx(nx_graph)
        assert back.directed == directed
        assert sorted(back.vertices()) == sorted(g.vertices())
        assert sorted(back.edges()) == sorted(g.edges())

    def test_default_weight(self):
        assert from_networkx(nx.path_graph(3), default_weight=2).weight(0, 1) == 2

    def test_vertex_names(self):
        names = vertex_names(28)
        assert names[:3] == ["A", "B", "C"] and names[25] == "Z" and names[26:] == ["V27", "V28"]


class TestLayouts:
    @pytest.mark.parametrize("layout", list(LAYOUTS))
    def test_positions_inside_canvas(self, layout):
        g = GridGenerator().generate(9, seed=1)
        positions = compute_layout(g, layout, seed=1)
        assert set(positions) == set(g.vertices())
        for x, y in positions.values():
            assert 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0

    def test_normalize_uses_margins_and_flips_y(self):
        pos = normalize_positions({"a": (-1, -1), "b": (1, 1)}, margin=0.1)
        assert pos["a"] == pytest.approx((0.1, 0.9))
        assert pos["b"] == pytest.approx((0.9, 0.1))

    def test_degenerate_cases(self):
        assert normalize_positions({}) == {}
        assert normalize_positions({"a": (3, 3)}) == {"a": (0.5, 0.5)}
        assert compute_layout(Graph(), "Пружинна (spring)") == {}
        single = Graph()
        single.add_vertex("A")
        assert compute_layout(single, "Спектральна (spectral)") == {"A": (0.5, 0.5)}

    def test_spread_separates_close_vertices(self):
        pos = spread_positions({"a": (0.5, 0.5), "b": (0.5, 0.5), "c": (0.52, 0.5)}, min_distance=0.1)
        points = list(pos.values())
        for i, p in enumerate(points):
            for q in points[i + 1:]:
                assert ((p[0] - q[0]) ** 2 + (p[1] - q[1]) ** 2) ** 0.5 >= 0.1 - 1e-6
        far = {"a": (0.1, 0.1), "b": (0.9, 0.9)}
        assert spread_positions(far) == far

    def test_spread_respects_aspect(self):
        # На полотні 4:1 вертикальна відстань 0.1 - це в 4 рази менше пікселів, ніж горизонтальна
        pos = spread_positions({"a": (0.5, 0.45), "b": (0.5, 0.55)}, min_distance=0.15, aspect=4)
        assert abs(pos["a"][1] - pos["b"][1]) >= 0.15 - 1e-6

    def test_spring_layout_is_reproducible(self):
        g = RandomGraphGenerator().generate(8, seed=3)
        assert compute_layout(g, "Пружинна (spring)", seed=5) == compute_layout(g, "Пружинна (spring)", seed=5)


class TestGenerators:
    @pytest.mark.parametrize("title", list(GENERATORS))
    @pytest.mark.parametrize("n", [1, 2, 7, 12])
    def test_vertex_count_and_weights(self, title, n):
        g = GENERATORS[title].generate(n, seed=2)
        assert g.size == n
        assert g.vertices() == vertex_names(n)
        assert all(1 <= w <= 9 for _, _, w in g.edges())

    def test_shapes(self):
        assert len(TreeGenerator().generate(10, seed=0).edges()) == 9
        assert graph_metrics(TreeGenerator().generate(10, seed=0))["acyclic"]
        assert len(CompleteGenerator().generate(6).edges()) == 15
        grid = GridGenerator().generate(9)
        assert len(grid.edges()) == 12  # решітка 3x3
        assert RandomGraphGenerator(0.0).generate(5).edges() == []

    def test_reproducible(self):
        a = RandomGraphGenerator().generate(10, seed=4)
        b = RandomGraphGenerator().generate(10, seed=4)
        assert sorted(a.edges()) == sorted(b.edges())

    def test_invalid_size(self):
        with pytest.raises(ValueError):
            TreeGenerator().generate(0)


class TestMetrics:
    def test_undirected(self):
        m = graph_metrics(sample())
        assert m["vertices"] == 4 and m["edges"] == 3
        assert m["components"] == 2 and not m["connected"] and m["diameter"] is None
        assert m["density"] == pytest.approx(0.5)
        assert not m["acyclic"]

    def test_directed_and_empty(self):
        g = Graph(directed=True)
        g.add_edge("A", "B")
        g.add_edge("B", "A")
        m = graph_metrics(g)
        assert m["diameter"] == 1 and not m["acyclic"]
        assert graph_metrics(Graph())["vertices"] == 0


# ---------- звірка з networkx ----------

@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("directed", [False, True])
def test_bfs_matches_networkx(random_graph, seed, directed):
    g = random_graph(seed, directed=directed)
    reference = to_networkx(g)
    start = g.vertices()[0]
    order = BFS().execute(g, start)
    levels = nx.single_source_shortest_path_length(reference, start)
    assert set(order) == set(levels)
    assert len(order) == len(set(order))
    # BFS відвідує вершини шарами: рівні не спадають
    assert [levels[v] for v in order] == sorted(levels[v] for v in order)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("directed", [False, True])
def test_dfs_matches_networkx(random_graph, seed, directed):
    g = random_graph(seed, directed=directed)
    reference = to_networkx(g)
    start = g.vertices()[0]
    dfs = DFS()
    order = dfs.execute(g, start)
    assert set(order) == nx.descendants(reference, start) | {start}
    # ребра дерева DFS існують у графі, і їх рівно на одне менше за вершини
    tree = dfs.tree_edges()
    assert len(tree) == len(order) - 1
    assert all(reference.has_edge(u, v) for u, v in tree)


@pytest.mark.parametrize("seed", SEEDS)
@pytest.mark.parametrize("directed", [False, True])
def test_dijkstra_matches_networkx(random_graph, seed, directed):
    g = random_graph(seed, directed=directed)
    reference = to_networkx(g)
    start = g.vertices()[0]
    dijkstra = Dijkstra()
    distances = dijkstra.execute(g, start)
    expected = nx.single_source_dijkstra_path_length(reference, start)
    reachable = {v: d for v, d in distances.items() if d != float("inf")}
    assert reachable == pytest.approx(expected)
    for target, length in expected.items():
        path = dijkstra.path_to(target)
        assert path[0] == start and path[-1] == target
        assert nx.path_weight(reference, path, "weight") == pytest.approx(length)
