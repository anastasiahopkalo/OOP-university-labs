from itertools import count
from typing import Any, Dict, List

from src.core.algorithm import GraphAlgorithm
from src.data_structures.binary_heap import BinaryHeap


class Dijkstra(GraphAlgorithm):
    """Найкоротші шляхи від однієї вершини для графа з невід'ємними вагами.

    Пріоритетна черга - наша BinaryHeap. O((V + E) log V).
    """

    def __init__(self):
        super().__init__("Dijkstra")

    def _empty_result(self):
        return {}

    def _run(self, graph, start) -> Dict[Any, float]:
        if any(w < 0 for _, _, w in graph.edges()):
            raise ValueError("Алгоритм Дейкстри не працює з від'ємними вагами")

        order = count()  # щоб купа не порівнювала самі вершини при однакових відстанях
        heap = BinaryHeap()
        self._distances = {v: float("inf") for v in graph.vertices()}
        self._distances[start] = 0
        self._parent[start] = None
        heap.push((0, next(order), start))
        self._frontier = [start]
        self._record_step(f"Відстань до {start} = 0", "discover", start)

        while heap.size:
            dist, _, current = heap.pop()
            if current in self._visited:
                continue
            self._visited.append(current)
            self._frontier = self._heap_frontier(heap)
            self._record_step(f"Фіксуємо {current}: відстань {dist}", "visit", current)

            for neighbour in graph.neighbors(current):
                if neighbour in self._visited:
                    continue
                self._comparisons += 1
                candidate = dist + graph.weight(current, neighbour)
                if candidate < self._distances[neighbour]:
                    old = self._distances[neighbour]
                    self._distances[neighbour] = candidate
                    self._parent[neighbour] = current
                    self._swaps += 1
                    heap.push((candidate, next(order), neighbour))
                    self._frontier = self._heap_frontier(heap)
                    old_text = "∞" if old == float("inf") else old
                    self._record_step(f"Ребро {current}–{neighbour}: {old_text} → {candidate}",
                                      "relax", current, (current, neighbour))
                else:
                    self._record_step(f"Ребро {current}–{neighbour}: {candidate} ≥ "
                                      f"{self._distances[neighbour]}, без змін",
                                      "skip", current, (current, neighbour))

        return dict(self._distances)

    def _heap_frontier(self, heap: BinaryHeap) -> List:
        """Вершини в купі за зростанням відстані, без дублікатів і вже зафіксованих."""
        ordered = (v for _, _, v in sorted(heap.get_all()) if v not in self._visited)
        return list(dict.fromkeys(ordered))

    def path_to(self, target) -> List:
        """Найкоротший шлях від старту до target за результатами останнього execute()."""
        if target not in self._parent:
            return []
        path = []
        while target is not None:
            path.append(target)
            target = self._parent[target]
        return path[::-1]
