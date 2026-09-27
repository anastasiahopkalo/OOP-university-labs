from abc import ABC, abstractmethod
from typing import List, TypeVar
from dataclasses import dataclass

T = TypeVar('T')


@dataclass
class AlgorithmStep:
    action: str
    affected_indices: List[int]
    comparisons: int = 0
    swaps: int = 0


class Algorithm(ABC):
    def __init__(self, name: str):
        self._name = name
        self._steps = []
        self._comparisons = 0
        self._swaps = 0

    @property
    def name(self):
        return self._name

    @abstractmethod
    def execute(self, data: List[T]) -> List[T]:
        pass

    def get_statistics(self):
        return {
            "name": self._name,
            "steps": len(self._steps),
            "comparisons": self._comparisons,
            "swaps": self._swaps
        }


class SortingAlgorithm(Algorithm):
    def __init__(self, name: str):
        super().__init__(name)

    def _record_step(self, action: str, indices: List[int]):
        step = AlgorithmStep(action, indices, self._comparisons, self._swaps)
        self._steps.append(step)