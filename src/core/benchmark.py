"""Порівняння алгоритмів сортування на numpy (ЛР3).

numpy тут робить три речі:
    * генерує вхідні масиви (numpy.random.Generator з фіксованим seed - результати відтворювані);
    * рахує статистику повторних замірів (mean / std);
    * оцінює емпіричну складність: нахил прямої в log-log масштабі (numpy.polyfit)
      і найкращу модель c*f(n) методом найменших квадратів (numpy.linalg.lstsq).
"""
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Callable, Dict, List, Optional, Sequence, Tuple

import numpy as np

from src.core.algorithm import SortingAlgorithm


# ---------- генератори вхідних даних ----------

class InputGenerator(ABC):
    """Стратегія створення вхідного масиву розміру n."""

    key: str = ""
    title: str = ""

    @abstractmethod
    def generate(self, n: int, rng: np.random.Generator) -> np.ndarray:
        pass

    def __repr__(self) -> str:
        return f"{type(self).__name__}()"


class RandomInput(InputGenerator):
    key, title = "random", "Випадковий"

    def generate(self, n, rng):
        return rng.integers(0, max(10 * n, 10), size=n)


class SortedInput(InputGenerator):
    key, title = "sorted", "Відсортований"

    def generate(self, n, rng):
        return np.sort(rng.integers(0, max(10 * n, 10), size=n))


class ReversedInput(InputGenerator):
    key, title = "reversed", "Обернений"

    def generate(self, n, rng):
        return np.sort(rng.integers(0, max(10 * n, 10), size=n))[::-1]


class NearlySortedInput(InputGenerator):
    """Відсортований масив, у якому переставлено ~5% пар елементів."""
    key, title = "nearly_sorted", "Майже відсортований"

    def __init__(self, fraction: float = 0.05):
        self.fraction = fraction

    def generate(self, n, rng):
        data = np.arange(n)
        swaps = int(n * self.fraction)
        if n > 1 and swaps:
            i = rng.integers(0, n, size=swaps)
            j = rng.integers(0, n, size=swaps)
            for a, b in zip(i, j):
                data[a], data[b] = data[b], data[a]
        return data


class FewUniqueInput(InputGenerator):
    key, title = "few_unique", "Мало унікальних"

    def generate(self, n, rng):
        return rng.integers(0, 5, size=n)


INPUT_GENERATORS: Dict[str, InputGenerator] = {
    g.key: g for g in (RandomInput(), SortedInput(), ReversedInput(),
                       NearlySortedInput(), FewUniqueInput())
}


def make_sizes(minimum: int, maximum: int, points: int) -> List[int]:
    """Рівномірна сітка розмірів без повторів: make_sizes(100, 500, 5) -> [100, 200, ..., 500]."""
    if minimum < 1 or maximum < minimum or points < 1:
        raise ValueError("Некоректний діапазон розмірів")
    return sorted({int(round(n)) for n in np.linspace(minimum, maximum, points)})


# ---------- результати ----------

@dataclass
class BenchmarkResult:
    algorithm: str
    input_kind: str
    size: int
    times: np.ndarray
    comparisons: float
    swaps: float

    @property
    def mean_time(self) -> float:
        return float(np.mean(self.times))

    @property
    def std_time(self) -> float:
        return float(np.std(self.times, ddof=1)) if len(self.times) > 1 else 0.0

    def metric(self, name: str) -> float:
        return {"time": self.mean_time, "comparisons": self.comparisons, "swaps": self.swaps}[name]


METRICS = {"time": "Час, с", "comparisons": "Порівняння", "swaps": "Обміни / записи"}


# ---------- оцінка складності ----------

COMPLEXITY_MODELS: Dict[str, Callable[[np.ndarray], np.ndarray]] = {
    "O(n)": lambda n: n,
    "O(n log n)": lambda n: n * np.log2(n),
    "O(n²)": lambda n: n ** 2,
}


@dataclass
class ComplexityEstimate:
    exponent: float        # k у v ≈ c·n^k (нахил у log-log)
    best_model: str        # найближча з COMPLEXITY_MODELS
    coefficient: float     # c для найкращої моделі
    errors: Dict[str, float] = field(default_factory=dict)  # відносна похибка кожної моделі


def estimate_complexity(sizes: Sequence[float], values: Sequence[float]) -> Optional[ComplexityEstimate]:
    """Підбирає модель складності за точками (n, значення). None, якщо даних замало."""
    n = np.asarray(sizes, dtype=float)
    v = np.asarray(values, dtype=float)
    mask = (n > 1) & (v > 0)
    n, v = n[mask], v[mask]
    if len(np.unique(n)) < 2:
        return None

    exponent = float(np.polyfit(np.log(n), np.log(v), 1)[0])

    errors: Dict[str, float] = {}
    coefficients: Dict[str, float] = {}
    for name, model in COMPLEXITY_MODELS.items():
        f = model(n).reshape(-1, 1)
        # Відносна похибка, щоб великі n не домінували: ділимо обидві частини на v
        (c,), *_ = np.linalg.lstsq(f / v[:, None], np.ones_like(v), rcond=None)
        coefficients[name] = float(c)
        errors[name] = float(np.sqrt(np.mean((c * f[:, 0] / v - 1) ** 2)))
    best = min(errors, key=errors.get)
    return ComplexityEstimate(exponent, best, coefficients[best], errors)


# ---------- бенчмарк ----------

class Benchmark:
    """Заміряє кілька алгоритмів на однакових вхідних даних.

    Для кожного розміру генерується `repeats` масивів, і всі алгоритми сортують
    ті самі масиви - так порівняння чесне.
    """

    def __init__(self, algorithms: Sequence[Callable[[], SortingAlgorithm]], sizes: Sequence[int],
                 generator: InputGenerator = RandomInput(), repeats: int = 3, seed: int = 42):
        if not algorithms:
            raise ValueError("Потрібен хоча б один алгоритм")
        if repeats < 1:
            raise ValueError("Кількість повторів має бути >= 1")
        self._factories = list(algorithms)
        self._sizes = sorted(set(int(n) for n in sizes))
        if not self._sizes or self._sizes[0] < 0:
            raise ValueError("Потрібен хоча б один невід'ємний розмір")
        self._generator = generator
        self._repeats = repeats
        self._seed = seed

    @property
    def total_runs(self) -> int:
        return len(self._factories) * len(self._sizes) * self._repeats

    def run(self, on_progress: Optional[Callable[[int, int], None]] = None,
            should_stop: Optional[Callable[[], bool]] = None) -> List[BenchmarkResult]:
        rng = np.random.default_rng(self._seed)
        results: List[BenchmarkResult] = []
        done = 0
        for size in self._sizes:
            inputs = [self._generator.generate(size, rng).tolist() for _ in range(self._repeats)]
            for factory in self._factories:
                times, comparisons, swaps = [], [], []
                name = ""
                for data in inputs:
                    if should_stop is not None and should_stop():
                        return results
                    algorithm = factory()
                    algorithm.record_steps = False
                    name = algorithm.name
                    start = time.perf_counter()
                    output = algorithm.execute(data)
                    times.append(time.perf_counter() - start)
                    if output != sorted(data):
                        raise AssertionError(f"{name} відсортував неправильно")
                    stats = algorithm.get_statistics()
                    comparisons.append(stats["comparisons"])
                    swaps.append(stats["swaps"])
                    done += 1
                    if on_progress is not None:
                        on_progress(done, self.total_runs)
                results.append(BenchmarkResult(name, self._generator.key, size, np.array(times),
                                               float(np.mean(comparisons)), float(np.mean(swaps))))
        return results


def series(results: Sequence[BenchmarkResult], metric: str) -> Dict[str, Tuple[np.ndarray, np.ndarray]]:
    """{алгоритм: (розміри, значення метрики)} - зручно для графіка й оцінки складності."""
    grouped: Dict[str, List[Tuple[int, float]]] = {}
    for r in results:
        grouped.setdefault(r.algorithm, []).append((r.size, r.metric(metric)))
    return {name: (np.array([p[0] for p in sorted(points)]), np.array([p[1] for p in sorted(points)]))
            for name, points in grouped.items()}
