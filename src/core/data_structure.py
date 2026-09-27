from abc import ABC, abstractmethod
from typing import Generic, TypeVar, List

T = TypeVar('T')


class DataStructure(ABC, Generic[T]):
    def __init__(self, name: str):
        self._name = name
        self._size = 0

    @property
    def size(self):
        return self._size

    @abstractmethod
    def insert(self, data: T, position: int = None):
        pass

    @abstractmethod
    def delete(self, position: int) -> T:
        pass

    @abstractmethod
    def find(self, target: T) -> int:
        pass

    @abstractmethod
    def get_all(self) -> List[T]:
        pass