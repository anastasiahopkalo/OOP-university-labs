from abc import ABC, abstractmethod
from typing import List, TypeVar, Any, Dict, Optional, Tuple
from dataclasses import dataclass, field

T = TypeVar('T')


@dataclass
class AlgorithmStep:
    action: str
    affected_indices: List[int]
    comparisons: int = 0
    swaps: int = 0
    # Тип кроку: "compare", "swap", "set", "done" - використовується GUI для підсвічування
    kind: str = "swap"
    # Стан масиву після кроку - потрібен для покрокової анімації
    snapshot: List = field(default_factory=list)


class Algorithm(ABC):
    def __init__(self, name: str):
        self._name = name
        self._steps = []
        self._comparisons = 0
        self._swaps = 0

    @property
    def name(self):
        return self._name

    @property
    def steps(self) -> List[AlgorithmStep]:
        return list(self._steps)

    @abstractmethod
    def execute(self, data: List[T]) -> List[T]:
        pass

    def _reset(self):
        self._steps = []
        self._comparisons = 0
        self._swaps = 0

    def get_statistics(self):
        return {
            "name": self._name,
            "steps": len(self._steps),
            "comparisons": self._comparisons,
            "swaps": self._swaps
        }


class SortingAlgorithm(Algorithm):
    """Шаблонний метод: execute() готує дані, а підкласи реалізують лише _sort()."""

    def __init__(self, name: str):
        super().__init__(name)
        self._array = []

    def execute(self, data: List[T]) -> List[T]:
        self._reset()
        self._array = list(data)
        self._sort(self._array)
        self._record_step("Sorted", list(range(len(self._array))), kind="done")
        return self._array

    @abstractmethod
    def _sort(self, arr: List[T]) -> None:
        """Сортує arr на місці, записуючи кроки через _record_step()."""
        pass

    def _record_step(self, action: str, indices: List[int], kind: str = "swap"):
        step = AlgorithmStep(action, indices, self._comparisons, self._swaps,
                             kind, list(self._array))
        self._steps.append(step)


@dataclass
class GraphStep:
    """Крок алгоритму на графі - знімок стану для покрокової анімації."""
    action: str
    # "visit", "edge", "discover", "skip", "relax", "done"
    kind: str
    current: Any = None
    edge: Optional[Tuple[Any, Any]] = None
    visited: List = field(default_factory=list)
    frontier: List = field(default_factory=list)
    distances: Dict = field(default_factory=dict)
    tree_edges: List[Tuple[Any, Any]] = field(default_factory=list)
    comparisons: int = 0


class GraphAlgorithm(Algorithm):
    """Шаблонний метод для алгоритмів на графах: execute() перевіряє вхід
    і готує стан, а підкласи реалізують лише _run()."""

    def __init__(self, name: str):
        super().__init__(name)
        self._visited: List = []
        self._frontier: List = []
        self._distances: Dict = {}
        self._parent: Dict = {}

    def execute(self, graph, start=None):
        self._reset()
        self._visited, self._frontier, self._distances, self._parent = [], [], {}, {}
        if graph.size == 0:
            return self._empty_result()
        if start is None:
            start = graph.vertices()[0]
        if graph.find(start) == -1:
            raise ValueError(f"Вершини {start!r} немає в графі")
        result = self._run(graph, start)
        self._record_step("Готово", "done")
        return result

    @abstractmethod
    def _run(self, graph, start):
        pass

    def _empty_result(self):
        return []

    @property
    def parents(self) -> Dict:
        return dict(self._parent)

    def tree_edges(self) -> List[Tuple[Any, Any]]:
        """Ребра дерева обходу (або дерева найкоротших шляхів)."""
        return [(p, v) for v, p in self._parent.items() if p is not None]

    def _record_step(self, action: str, kind: str, current=None, edge=None):
        self._steps.append(GraphStep(
            action, kind, current, edge,
            list(self._visited), list(self._frontier), dict(self._distances),
            self.tree_edges(), self._comparisons,
        ))
