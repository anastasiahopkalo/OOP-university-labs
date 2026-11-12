"""Міст між нашим Graph і бібліотекою networkx (ЛР3).

networkx використовується для:
    * розкладки вершин на полотні (spring, circular, shell, kamada-kawai, spectral);
    * генерації випадкових графів (Erdős–Rényi, дерево, решітка, повний граф);
    * метрик графа (зв'язність, компоненти, діаметр, щільність);
    * перевірки наших BFS / DFS / Dijkstra у тестах.
"""
import random
from abc import ABC, abstractmethod
from string import ascii_uppercase
from typing import Any, Callable, Dict, List, Tuple, Union

import networkx as nx

from src.data_structures.graph import Graph

Positions = Dict[Any, Tuple[float, float]]
NxGraph = Union[nx.Graph, nx.DiGraph]


# ---------- конвертація ----------

def to_networkx(graph: Graph) -> NxGraph:
    """Наш Graph -> nx.Graph / nx.DiGraph; вага ребра в атрибуті weight."""
    result = nx.DiGraph() if graph.directed else nx.Graph()
    result.add_nodes_from(graph.vertices())
    result.add_weighted_edges_from(graph.edges())
    return result


def from_networkx(nx_graph: NxGraph, default_weight: float = 1) -> Graph:
    """nx.Graph / nx.DiGraph -> наш Graph (без атрибута weight береться default_weight)."""
    result = Graph(directed=nx_graph.is_directed())
    for vertex in nx_graph.nodes:
        result.add_vertex(vertex)
    for u, v, data in nx_graph.edges(data=True):
        result.add_edge(u, v, data.get("weight", default_weight))
    return result


def vertex_names(count: int) -> List[str]:
    """A, B, ..., Z, V27, V28, ... - ті самі назви, що й при ручному додаванні вершин."""
    return [ascii_uppercase[i] if i < 26 else f"V{i + 1}" for i in range(count)]


# ---------- розкладки ----------

LAYOUTS: Dict[str, Callable[..., Positions]] = {
    "Пружинна (spring)": lambda g, seed: nx.spring_layout(g, seed=seed),
    "Колова (circular)": lambda g, seed: nx.circular_layout(g),
    "Концентрична (shell)": lambda g, seed: nx.shell_layout(g),
    "Kamada–Kawai": lambda g, seed: nx.kamada_kawai_layout(g),
    "Спектральна (spectral)": lambda g, seed: nx.spectral_layout(g),
}


def normalize_positions(positions: Positions, margin: float = 0.08) -> Positions:
    """Масштабує координати networkx (приблизно [-1, 1]) у частки полотна [margin, 1 - margin]."""
    if not positions:
        return {}
    xs = [float(p[0]) for p in positions.values()]
    ys = [float(p[1]) for p in positions.values()]
    span = 1 - 2 * margin

    def scale(value: float, low: float, high: float) -> float:
        return 0.5 if high - low < 1e-9 else margin + (value - low) / (high - low) * span

    # y у networkx росте вгору, а на полотні - вниз
    return {v: (scale(float(p[0]), min(xs), max(xs)), 1 - scale(float(p[1]), min(ys), max(ys)))
            for v, p in positions.items()}


def compute_layout(graph: Graph, layout: str, seed: int = 0) -> Positions:
    """Позиції вершин у частках полотна для вибраної розкладки."""
    if graph.size == 0:
        return {}
    nx_graph = to_networkx(graph)
    if graph.size < 3 and layout.startswith("Спектральна"):
        layout = "Колова (circular)"  # спектральна розкладка вироджена для 1-2 вершин
    try:
        positions = LAYOUTS[layout](nx_graph, seed)
    except (nx.NetworkXException, ValueError, ImportError):
        positions = nx.circular_layout(nx_graph)
    return normalize_positions(positions)


# ---------- генератори ----------

class GraphGenerator(ABC):
    """Стратегія створення випадкового графа з n вершинами."""

    title: str = ""

    @abstractmethod
    def _build(self, n: int, seed: int) -> nx.Graph:
        pass

    def generate(self, n: int, seed: int = 0, max_weight: int = 9) -> Graph:
        if n < 1:
            raise ValueError("Кількість вершин має бути >= 1")
        nx_graph = self._build(n, seed)
        nx_graph = nx.relabel_nodes(nx_graph, dict(zip(nx_graph.nodes, vertex_names(nx_graph.number_of_nodes()))))
        rng = random.Random(seed)
        for u, v in nx_graph.edges:
            nx_graph.edges[u, v]["weight"] = rng.randint(1, max_weight)
        return from_networkx(nx_graph)


class RandomGraphGenerator(GraphGenerator):
    """Модель Ердеша–Реньї G(n, p): кожне ребро існує з імовірністю p."""
    title = "Випадковий (Erdős–Rényi)"

    def __init__(self, probability: float = 0.3):
        self.probability = probability

    def _build(self, n, seed):
        return nx.gnp_random_graph(n, self.probability, seed=seed)


class TreeGenerator(GraphGenerator):
    title = "Випадкове дерево"

    def _build(self, n, seed):
        if n == 1:
            return nx.empty_graph(1)
        return nx.random_labeled_tree(n, seed=seed)


class GridGenerator(GraphGenerator):
    """Решітка, наближена до квадратної, з рівно n вершинами (останній рядок може бути неповним)."""
    title = "Решітка"

    def _build(self, n, seed):
        columns = max(1, round(n ** 0.5))
        rows = -(-n // columns)
        grid = nx.grid_2d_graph(rows, columns)
        keep = sorted(grid.nodes)[:n]
        return nx.convert_node_labels_to_integers(grid.subgraph(keep).copy(), ordering="sorted")


class CompleteGenerator(GraphGenerator):
    title = "Повний граф"

    def _build(self, n, seed):
        return nx.complete_graph(n)


GENERATORS: Dict[str, GraphGenerator] = {
    g.title: g for g in (RandomGraphGenerator(), TreeGenerator(), GridGenerator(), CompleteGenerator())
}


# ---------- метрики ----------

def graph_metrics(graph: Graph) -> Dict[str, Any]:
    """Короткі характеристики графа, пораховані networkx."""
    nx_graph = to_networkx(graph)
    n = nx_graph.number_of_nodes()
    if n == 0:
        return {"vertices": 0, "edges": 0, "components": 0, "connected": False,
                "diameter": None, "density": 0.0, "acyclic": True}
    undirected = nx_graph.to_undirected()
    connected = nx.is_connected(undirected)
    diameter = None
    if nx_graph.is_directed():
        if nx.is_strongly_connected(nx_graph):
            diameter = nx.diameter(nx_graph)
        acyclic = nx.is_directed_acyclic_graph(nx_graph)
    else:
        if connected:
            diameter = nx.diameter(nx_graph)
        acyclic = nx.is_forest(nx_graph)
    return {
        "vertices": n,
        "edges": nx_graph.number_of_edges(),
        "components": nx.number_connected_components(undirected),
        "connected": connected,
        "diameter": diameter,
        "density": nx.density(nx_graph),
        "acyclic": acyclic,
    }
