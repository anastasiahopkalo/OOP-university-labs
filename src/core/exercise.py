import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from src.core.algorithm import Algorithm
from src.core.sandbox import run_code
from typing import Any, List, TypeVar

T = TypeVar('T')


@dataclass
class TestCase:
    __test__ = False  # щоб pytest не вважав клас тестом

    args: tuple
    expected: Any


@dataclass
class TestCaseResult:
    __test__ = False

    args: tuple
    expected: Any
    actual: Any
    passed: bool
    status: str          # "ok", "error", "timeout"
    elapsed: float


@dataclass
class ExerciseResult:
    passed: bool
    score: int
    message: str
    execution_time: float
    details: List[TestCaseResult] = field(default_factory=list)


class BaseExercise(ABC):
    """Спільна основа для всіх вправ: назва, складність, лічильник спроб."""

    def __init__(self, title: str, difficulty: str = "Легка"):
        self.title = title
        self.difficulty = difficulty
        self.attempts = 0

    @abstractmethod
    def execute(self, *args) -> ExerciseResult:
        pass


class Exercise(BaseExercise):
    """Вправа "відсортуй дані заданим алгоритмом" (з ЛР1)."""

    def __init__(self, title: str, algorithm: Algorithm, test_data: List[T]):
        super().__init__(title)
        self.algorithm = algorithm
        self.test_data = test_data

    def execute(self) -> ExerciseResult:
        self.attempts += 1
        start = time.perf_counter()
        try:
            result = self.algorithm.execute(self.test_data)
            expected = sorted(self.test_data)
            passed = result == expected
            return ExerciseResult(
                passed=passed,
                score=100 if passed else 50,
                message="✓ Passed!" if passed else "✗ Failed",
                execution_time=time.perf_counter() - start
            )
        except Exception as e:
            return ExerciseResult(
                passed=False,
                score=0,
                message=f"Error: {str(e)}",
                execution_time=0.0
            )


class CodeExercise(BaseExercise):
    """Вправа, де користувач пише функцію, а вона перевіряється на тест-кейсах."""

    def __init__(self, title: str, description: str, template: str, test_cases: List[TestCase],
                 difficulty: str = "Легка", function_name: str = "solve", hint: str = "",
                 timeout: float = 3.0):
        super().__init__(title, difficulty)
        if not test_cases:
            raise ValueError("Вправа повинна мати хоча б один тест")
        self.description = description
        self.template = template
        self.test_cases = list(test_cases)
        self.function_name = function_name
        self.hint = hint
        self.timeout = timeout

    def execute(self, code: str) -> ExerciseResult:
        self.attempts += 1
        start = time.perf_counter()
        report = run_code(code, self.function_name, [case.args for case in self.test_cases], self.timeout)
        elapsed = time.perf_counter() - start

        if report.error:
            return ExerciseResult(False, 0, f"Помилка: {report.error}", elapsed)

        details = []
        for case, outcome in zip(self.test_cases, report.outcomes):
            passed = outcome.status == "ok" and outcome.value == case.expected
            details.append(TestCaseResult(case.args, case.expected, outcome.value,
                                          passed, outcome.status, outcome.elapsed))

        passed_count = sum(d.passed for d in details)
        total = len(self.test_cases)
        score = round(100 * passed_count / total)
        all_passed = passed_count == total
        message = "✓ Усі тести пройдено!" if all_passed else f"Пройдено {passed_count} з {total} тестів"
        return ExerciseResult(all_passed, score, message, elapsed, details)
