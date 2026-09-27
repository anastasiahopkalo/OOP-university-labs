from dataclasses import dataclass
from src.core.algorithm import Algorithm
from typing import List, TypeVar

T = TypeVar('T')


@dataclass
class ExerciseResult:
    passed: bool
    score: int
    message: str
    execution_time: float


class Exercise:
    def __init__(self, title: str, algorithm: Algorithm, test_data: List[T]):
        self.title = title
        self.algorithm = algorithm
        self.test_data = test_data
        self.attempts = 0

    def execute(self) -> ExerciseResult:
        self.attempts += 1
        try:
            result = self.algorithm.execute(self.test_data)
            expected = sorted(self.test_data)
            passed = result == expected
            return ExerciseResult(
                passed=passed,
                score=100 if passed else 50,
                message="✓ Passed!" if passed else "✗ Failed",
                execution_time=0.001
            )
        except Exception as e:
            return ExerciseResult(
                passed=False,
                score=0,
                message=f"Error: {str(e)}",
                execution_time=0.0
            )