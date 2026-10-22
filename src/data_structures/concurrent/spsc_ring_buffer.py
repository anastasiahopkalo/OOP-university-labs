from multiprocessing import shared_memory
from typing import Optional


class SPSCRingBuffer:
    """Кільцевий буфер для одного виробника і одного споживача (SPSC)
    у спільній пам'яті між процесами - без жодних блокувань.

    Розмітка пам'яті (64-бітні цілі):
        [0] head - індекс наступного елемента для читання (пише лише споживач)
        [1] tail - індекс наступної вільної комірки (пише лише виробник)
        [2..] комірки даних

    Кожен індекс змінює лише один процес, тому CAS не потрібен:
    виробник спочатку записує дані, а потім публікує новий tail;
    споживач спочатку читає дані, а потім звільняє комірку, збільшуючи head.
    Порядок записів гарантує модель пам'яті x86 (TSO); на ARM для такого
    буфера в C знадобилися б бар'єри пам'яті.

    Об'єкт можна передати в інший процес (multiprocessing): там він
    під'єднається до тієї ж спільної пам'яті за її ім'ям.
    """

    HEADER = 2
    ITEM_SIZE = 8

    def __init__(self, capacity: int = 1024, name: Optional[str] = None):
        if name is None:
            if capacity < 1:
                raise ValueError("Місткість має бути додатною")
            size = (self.HEADER + capacity) * self.ITEM_SIZE
            self._shm = shared_memory.SharedMemory(create=True, size=size)
            self._owner = True
        else:
            try:
                # track=False (Python 3.13+): пам'ятю керує власник, а не цей процес
                self._shm = shared_memory.SharedMemory(name=name, track=False)
            except TypeError:
                self._shm = shared_memory.SharedMemory(name=name)
            self._owner = False
        self._cells = self._shm.buf.cast("q")
        self._capacity = capacity
        if self._owner:
            self._cells[0] = 0
            self._cells[1] = 0

    def __reduce__(self):
        # При передачі в інший процес надсилаємо лише ім'я і місткість
        return (self.__class__, (self._capacity, self._shm.name))

    @property
    def name(self) -> str:
        return self._shm.name

    @property
    def capacity(self) -> int:
        return self._capacity

    def __len__(self) -> int:
        return self._cells[1] - self._cells[0]

    def is_empty(self) -> bool:
        return len(self) == 0

    def is_full(self) -> bool:
        return len(self) >= self._capacity

    def try_put(self, value: int) -> bool:
        """Неблокуюча вставка: повертає False, якщо буфер повний."""
        tail = self._cells[1]
        if tail - self._cells[0] >= self._capacity:
            return False
        self._cells[self.HEADER + tail % self._capacity] = value
        self._cells[1] = tail + 1  # публікуємо лише після запису даних
        return True

    def try_get(self) -> Optional[int]:
        """Неблокуюче читання: повертає None, якщо буфер порожній."""
        head = self._cells[0]
        if head == self._cells[1]:
            return None
        value = self._cells[self.HEADER + head % self._capacity]
        self._cells[0] = head + 1  # звільняємо комірку лише після читання
        return value

    def close(self):
        """Від'єднується від пам'яті; власник також звільняє її."""
        if self._cells is None:
            return
        self._cells.release()
        self._cells = None
        self._shm.close()
        if self._owner:
            self._shm.unlink()

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        self.close()
