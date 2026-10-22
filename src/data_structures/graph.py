from src.core.data_structure import DataStructure
from typing import TypeVar, List, Dict, Tuple, Optional

T = TypeVar('T')


class Graph(DataStructure[T]):
    """Граф на списках суміжності. Підтримує орієнтовані/неорієнтовані та зважені ребра."""

    def __init__(self, directed: bool = False):
        super().__init__("DirectedGraph" if directed else "Graph")
        self._directed = directed
        self._adjacency: Dict[T, Dict[T, float]] = {}

    @property
    def directed(self) -> bool:
        return self._directed

    def add_vertex(self, vertex: T):
        if vertex not in self._adjacency:
            self._adjacency[vertex] = {}
            self._size += 1

    def remove_vertex(self, vertex: T) -> bool:
        if vertex not in self._adjacency:
            return False
        del self._adjacency[vertex]
        for neighbours in self._adjacency.values():
            neighbours.pop(vertex, None)
        self._size -= 1
        return True

    def add_edge(self, u: T, v: T, weight: float = 1):
        self.add_vertex(u)
        self.add_vertex(v)
        self._adjacency[u][v] = weight
        if not self._directed:
            self._adjacency[v][u] = weight

    def remove_edge(self, u: T, v: T) -> bool:
        if u not in self._adjacency or v not in self._adjacency[u]:
            return False
        del self._adjacency[u][v]
        if not self._directed:
            self._adjacency[v].pop(u, None)
        return True

    def has_edge(self, u: T, v: T) -> bool:
        return u in self._adjacency and v in self._adjacency[u]

    def weight(self, u: T, v: T) -> Optional[float]:
        return self._adjacency.get(u, {}).get(v)

    def neighbors(self, vertex: T) -> List[T]:
        return list(self._adjacency.get(vertex, {}))

    def degree(self, vertex: T) -> int:
        return len(self._adjacency.get(vertex, {}))

    def vertices(self) -> List[T]:
        return list(self._adjacency)

    def edges(self) -> List[Tuple[T, T, float]]:
        result = []
        seen = set()
        for u, neighbours in self._adjacency.items():
            for v, w in neighbours.items():
                if not self._directed:
                    key = frozenset((u, v))
                    if key in seen:
                        continue
                    seen.add(key)
                result.append((u, v, w))
        return result

    # Реалізація абстрактних методів базового класу
    def insert(self, data: T, position: int = None):
        self.add_vertex(data)

    def delete(self, position: int) -> Optional[T]:
        vertices = self.vertices()
        if not 0 <= position < len(vertices):
            return None
        vertex = vertices[position]
        self.remove_vertex(vertex)
        return vertex

    def find(self, target: T) -> int:
        vertices = self.vertices()
        return vertices.index(target) if target in self._adjacency else -1

    def get_all(self) -> List[T]:
        return self.vertices()
