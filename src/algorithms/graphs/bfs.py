from src.core.algorithm import GraphAlgorithm
from src.data_structures.queue import Queue


class BFS(GraphAlgorithm):
    """Пошук у ширину: обходить граф шарами за допомогою черги. O(V + E)."""

    def __init__(self):
        super().__init__("BFS")

    def _run(self, graph, start):
        queue = Queue()
        queue.enqueue(start)
        self._parent[start] = None
        self._distances[start] = 0
        self._frontier = queue.get_all()
        self._record_step(f"Додаємо {start} у чергу", "discover", start)

        while queue.size:
            current = queue.dequeue()
            self._visited.append(current)
            self._frontier = queue.get_all()
            self._record_step(f"Відвідуємо {current} (рівень {self._distances[current]})", "visit", current)

            for neighbour in graph.neighbors(current):
                self._comparisons += 1
                if neighbour in self._parent:
                    self._record_step(f"Ребро {current}–{neighbour}: {neighbour} вже знайдено",
                                      "skip", current, (current, neighbour))
                    continue
                self._parent[neighbour] = current
                self._distances[neighbour] = self._distances[current] + 1
                queue.enqueue(neighbour)
                self._frontier = queue.get_all()
                self._record_step(f"Ребро {current}–{neighbour}: додаємо {neighbour} у чергу",
                                  "discover", current, (current, neighbour))

        return list(self._visited)
