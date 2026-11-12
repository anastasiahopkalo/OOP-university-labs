"""Граф знань курсу на networkx (ЛР3).

Вершини - теми, ребра - передумови (тема A → тема B: спершу треба пройти A).
Тема з вправами вважається пройденою, коли розв'язано всі її вправи.
Тема без вправ (теорія у відповідній вкладці) зараховується, щойно вона стала доступною.
"""
from dataclasses import dataclass, field
from typing import Dict, Iterable, List, Optional, Set, Tuple

import networkx as nx

from src.core.analytics import ProgressTracker

MASTERED, AVAILABLE, LOCKED = "mastered", "available", "locked"


@dataclass(frozen=True)
class Topic:
    key: str
    title: str
    tab: str                                   # де вивчати в програмі
    exercises: Tuple[str, ...] = field(default=())

    @property
    def is_theory(self) -> bool:
        return not self.exercises


DEFAULT_TOPICS: List[Topic] = [
    Topic("arrays", "Масиви", "Вправи", ("Максимальний елемент", "Розворот списку")),
    Topic("binary_search", "Бінарний пошук", "Вправи", ("Бінарний пошук",)),
    Topic("simple_sorts", "Прості сортування", "Сортування", ("Сортування бульбашкою",)),
    Topic("stack_queue", "Стек і черга", "Структури даних", ("Правильні дужки",)),
    Topic("merge_sort", "Сортування злиттям", "Сортування", ("Злиття відсортованих списків",)),
    Topic("quick_sort", "Швидке сортування", "Сортування"),
    Topic("trees_heaps", "Дерева і купи", "Структури даних"),
    Topic("heap_sort", "Пірамідальне сортування", "Сортування"),
    Topic("graph_traversal", "Обходи графів", "Графи", ("Компоненти зв'язності",)),
    Topic("dijkstra", "Алгоритм Дейкстри", "Графи"),
    Topic("complexity", "Порівняння складності", "Порівняння"),
]

DEFAULT_PREREQUISITES: List[Tuple[str, str]] = [
    ("arrays", "binary_search"),
    ("arrays", "simple_sorts"),
    ("arrays", "stack_queue"),
    ("simple_sorts", "merge_sort"),
    ("simple_sorts", "quick_sort"),
    ("binary_search", "trees_heaps"),
    ("trees_heaps", "heap_sort"),
    ("simple_sorts", "heap_sort"),
    ("stack_queue", "graph_traversal"),
    ("graph_traversal", "dijkstra"),
    ("trees_heaps", "dijkstra"),
    ("merge_sort", "complexity"),
    ("quick_sort", "complexity"),
]


class KnowledgeGraph:
    def __init__(self, topics: Iterable[Topic] = DEFAULT_TOPICS,
                 prerequisites: Iterable[Tuple[str, str]] = DEFAULT_PREREQUISITES):
        self._graph = nx.DiGraph()
        for topic in topics:
            self._graph.add_node(topic.key, topic=topic)
        for before, after in prerequisites:
            for key in (before, after):
                if key not in self._graph:
                    raise ValueError(f"Невідома тема {key!r}")
            self._graph.add_edge(before, after)
        if not nx.is_directed_acyclic_graph(self._graph):
            cycle = nx.find_cycle(self._graph)
            raise ValueError(f"Передумови утворюють цикл: {cycle}")

    @property
    def graph(self) -> nx.DiGraph:
        return self._graph

    def topic(self, key: str) -> Topic:
        return self._graph.nodes[key]["topic"]

    def topics(self) -> List[Topic]:
        return [self.topic(k) for k in self.topological_order()]

    def prerequisites(self, key: str) -> List[str]:
        return sorted(self._graph.predecessors(key))

    def all_prerequisites(self, key: str) -> Set[str]:
        return nx.ancestors(self._graph, key)

    def topological_order(self) -> List[str]:
        """Порядок вивчення, у якому кожна тема йде після своїх передумов (стабільний)."""
        return list(nx.lexicographical_topological_sort(self._graph, key=self._order_key))

    def levels(self) -> List[List[str]]:
        """Рівні графа: теми, які можна вивчати паралельно (topological_generations)."""
        return [sorted(level, key=self._order_key) for level in nx.topological_generations(self._graph)]

    def exercise_titles(self) -> Set[str]:
        return {title for topic in self.topics() for title in topic.exercises}

    def _order_key(self, key: str) -> int:
        return list(self._graph.nodes).index(key)

    # ---------- прогрес студента ----------

    def statuses(self, tracker: ProgressTracker) -> Dict[str, str]:
        """{тема: MASTERED | AVAILABLE | LOCKED}."""
        solved = set(tracker.solved_exercises())
        passed: Set[str] = set()
        result: Dict[str, str] = {}
        for key in self.topological_order():
            topic = self.topic(key)
            if not all(p in passed for p in self._graph.predecessors(key)):
                result[key] = LOCKED
                continue
            if topic.is_theory:
                result[key] = AVAILABLE
                passed.add(key)  # теорію не блокуємо вправами
            elif all(title in solved for title in topic.exercises):
                result[key] = MASTERED
                passed.add(key)
            else:
                result[key] = AVAILABLE
        return result

    def mastered(self, tracker: ProgressTracker) -> List[str]:
        return [k for k, s in self.statuses(tracker).items() if s == MASTERED]

    def available(self, tracker: ProgressTracker) -> List[str]:
        return [k for k, s in self.statuses(tracker).items() if s == AVAILABLE]

    def topic_progress(self, key: str, tracker: ProgressTracker) -> Tuple[int, int]:
        """(розв'язано вправ теми, усього вправ теми)."""
        exercises = self.topic(key).exercises
        solved = set(tracker.solved_exercises())
        return sum(title in solved for title in exercises), len(exercises)

    def next_recommended(self, tracker: ProgressTracker) -> Optional[Topic]:
        """Перша доступна непройдена тема з вправами; якщо таких немає - перша доступна теорія."""
        available = [self.topic(k) for k in self.available(tracker)]
        practice = [t for t in available if not t.is_theory]
        if practice:
            return practice[0]
        return available[0] if available else None
