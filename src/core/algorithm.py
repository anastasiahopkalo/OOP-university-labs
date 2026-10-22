from abc import ABC, abstractmethod
from typing import List, TypeVar
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
