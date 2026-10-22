from src.core.data_structure import DataStructure
from typing import TypeVar, List, Any, Optional, Tuple

T = TypeVar('T')


class HashTable(DataStructure[T]):
    """Хеш-таблиця з методом ланцюжків (separate chaining) і автоматичним розширенням."""

    LOAD_FACTOR = 0.75

    def __init__(self, capacity: int = 8):
        super().__init__("HashTable")
        self._capacity = max(1, capacity)
        self._buckets: List[List[Tuple[T, Any]]] = [[] for _ in range(self._capacity)]

    @property
    def capacity(self) -> int:
        return self._capacity

    @property
    def load_factor(self) -> float:
        return self._size / self._capacity

    def _index(self, key: T) -> int:
        return hash(key) % self._capacity

    def _resize(self):
        old_items = self.items()
        self._capacity *= 2
        self._buckets = [[] for _ in range(self._capacity)]
        self._size = 0
        for key, value in old_items:
            self.put(key, value)

    def put(self, key: T, value: Any = None):
        bucket = self._buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                bucket[i] = (key, value)
                return
        bucket.append((key, value))
        self._size += 1
        if self.load_factor > self.LOAD_FACTOR:
            self._resize()

    def get(self, key: T, default: Any = None) -> Any:
        for k, v in self._buckets[self._index(key)]:
            if k == key:
                return v
        return default

    def remove(self, key: T) -> bool:
        bucket = self._buckets[self._index(key)]
        for i, (k, _) in enumerate(bucket):
            if k == key:
                del bucket[i]
                self._size -= 1
                return True
        return False

    def contains(self, key: T) -> bool:
        return self.find(key) != -1

    # data - ключ або пара (ключ, значення)
    def insert(self, data, position: int = None):
        if isinstance(data, tuple) and len(data) == 2:
            self.put(data[0], data[1])
        else:
            self.put(data)

    def delete(self, position: int) -> Optional[T]:
        """Видаляє ключ з індексом position у порядку get_all()."""
        keys = self.get_all()
        if not 0 <= position < len(keys):
            return None
        self.remove(keys[position])
        return keys[position]

    def find(self, target: T) -> int:
        """Повертає номер кошика, де лежить ключ, або -1."""
        index = self._index(target)
        return index if any(k == target for k, _ in self._buckets[index]) else -1

    def get_all(self) -> List[T]:
        return [k for bucket in self._buckets for k, _ in bucket]

    def items(self) -> List[Tuple[T, Any]]:
        return [pair for bucket in self._buckets for pair in bucket]

    def buckets(self) -> List[List[Tuple[T, Any]]]:
        """Копія кошиків - для візуалізації колізій."""
        return [list(b) for b in self._buckets]
