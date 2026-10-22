from src.core.algorithm import GraphAlgorithm


class DFS(GraphAlgorithm):
    """Пошук у глибину: йде якомога глибше, потім повертається назад. O(V + E).

    frontier у кроках - поточний стек викликів (шлях від старту).
    """

    def __init__(self):
        super().__init__("DFS")

    def _run(self, graph, start):
        self._parent[start] = None

        def visit(vertex):
            self._visited.append(vertex)
            self._frontier.append(vertex)
            self._record_step(f"Відвідуємо {vertex}", "visit", vertex)

            for neighbour in graph.neighbors(vertex):
                self._comparisons += 1
                if neighbour in self._parent:
                    self._record_step(f"Ребро {vertex}–{neighbour}: {neighbour} вже відвідано",
                                      "skip", vertex, (vertex, neighbour))
                    continue
                self._parent[neighbour] = vertex
                self._record_step(f"Ребро {vertex}–{neighbour}: заглиблюємось у {neighbour}",
                                  "discover", vertex, (vertex, neighbour))
                visit(neighbour)

            self._frontier.pop()
            self._record_step(f"{vertex} оброблено, повертаємось назад", "edge", vertex)

        visit(start)
        return list(self._visited)
