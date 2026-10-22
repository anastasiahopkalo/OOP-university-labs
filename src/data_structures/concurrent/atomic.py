import threading
from typing import Generic, TypeVar

T = TypeVar('T')


class AtomicReference(Generic[T]):
    """Посилання з атомарною операцією compare-and-set (CAS).

    У процесорах CAS - одна апаратна інструкція (наприклад, CMPXCHG на x86).
    Python такої інструкції не надає, тому тут вона емулюється найкоротшою
    можливою критичною секцією: лише порівняння й запис одного посилання.

    Важливо: lock-free алгоритми, побудовані на цьому класі, ніколи не тримають
    блокування під час своєї роботи - вони читають стан, готують зміни і
    пробують опублікувати їх одним CAS, а при невдачі повторюють спробу.
    Саме така схема робить їх неблокуючими на справжньому залізі.
    """

    def __init__(self, value: T = None):
        self._value = value
        self._guard = threading.Lock()  # моделює атомарність апаратної інструкції

    def get(self) -> T:
        # Читання одного посилання в CPython атомарне
        return self._value

    def set(self, value: T):
        self._value = value

    def compare_and_set(self, expected: T, new: T) -> bool:
        """Записує new, лише якщо поточне значення - той самий об'єкт, що expected."""
        with self._guard:
            if self._value is expected:
                self._value = new
                return True
            return False
