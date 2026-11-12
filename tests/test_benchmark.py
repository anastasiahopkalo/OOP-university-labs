"""Тести бенчмарку на numpy та збереження його результатів у БД."""
import numpy as np
import pytest

from src import BubbleSort, HeapSort, InsertionSort, MergeSort, QuickSort
from src.core.benchmark import (
    INPUT_GENERATORS, Benchmark, BenchmarkResult, NearlySortedInput, RandomInput, ReversedInput,
    SortedInput, estimate_complexity, make_sizes, series,
)
from src.database import AlgorithmRunRepository, Database, SqlProgressRepository


class TestInputGenerators:
    @pytest.mark.parametrize("key", list(INPUT_GENERATORS))
    def test_size_and_reproducible(self, key):
        gen = INPUT_GENERATORS[key]
        a = gen.generate(50, np.random.default_rng(1))
        b = gen.generate(50, np.random.default_rng(1))
        assert len(a) == 50
        assert np.array_equal(a, b)
        assert len(gen.generate(0, np.random.default_rng(1))) == 0

    def test_shapes(self):
        rng = np.random.default_rng(0)
        assert np.all(np.diff(SortedInput().generate(100, rng)) >= 0)
        assert np.all(np.diff(ReversedInput().generate(100, rng)) <= 0)
        nearly = NearlySortedInput(0.05).generate(1000, rng)
        assert sorted(nearly.tolist()) == list(range(1000))
        assert np.mean(nearly == np.arange(1000)) > 0.85
        assert len(np.unique(INPUT_GENERATORS["few_unique"].generate(500, rng))) <= 5


def test_make_sizes():
    assert make_sizes(100, 500, 5) == [100, 200, 300, 400, 500]
    assert make_sizes(10, 10, 4) == [10]
    for bad in [(0, 10, 3), (10, 5, 3), (1, 10, 0)]:
        with pytest.raises(ValueError):
            make_sizes(*bad)


class TestComplexity:
    sizes = np.array([100, 200, 400, 800, 1600])

    @pytest.mark.parametrize("values, expected, exponent", [
        (3 * sizes, "O(n)", 1.0),
        (0.5 * sizes * np.log2(sizes), "O(n log n)", 1.1),
        (0.5 * sizes ** 2, "O(n²)", 2.0),
    ])
    def test_exact_models(self, values, expected, exponent):
        est = estimate_complexity(self.sizes, values)
        assert est.best_model == expected
        assert est.exponent == pytest.approx(exponent, abs=0.1)
        assert est.errors[expected] == pytest.approx(0, abs=1e-9)

    def test_not_enough_data(self):
        assert estimate_complexity([100], [5]) is None
        assert estimate_complexity([100, 200], [0, 0]) is None


class TestBenchmark:
    def test_results_and_progress(self):
        calls = []
        bench = Benchmark([BubbleSort, MergeSort], [20, 10], repeats=2)
        results = bench.run(on_progress=lambda done, total: calls.append((done, total)))
        assert bench.total_runs == 8
        assert calls[-1] == (8, 8)
        assert [(r.algorithm, r.size) for r in results] == [
            ("BubbleSort", 10), ("MergeSort", 10), ("BubbleSort", 20), ("MergeSort", 20)]
        assert all(len(r.times) == 2 and r.mean_time >= 0 and r.std_time >= 0 for r in results)
        assert results[0].input_kind == "random"

    def test_same_seed_same_operation_counts(self):
        a = Benchmark([QuickSort], [50], seed=7).run()
        b = Benchmark([QuickSort], [50], seed=7).run()
        assert a[0].comparisons == b[0].comparisons

    def test_stop(self):
        results = Benchmark([BubbleSort], [10, 20, 30]).run(should_stop=lambda: True)
        assert results == []

    def test_validation(self):
        with pytest.raises(ValueError):
            Benchmark([], [10])
        with pytest.raises(ValueError):
            Benchmark([BubbleSort], [10], repeats=0)
        with pytest.raises(ValueError):
            Benchmark([BubbleSort], [])

    def test_detects_quadratic_and_nlogn(self):
        results = Benchmark([BubbleSort, MergeSort, HeapSort], [64, 128, 256, 512], repeats=1).run()
        data = series(results, "comparisons")
        assert estimate_complexity(*data["BubbleSort"]).best_model == "O(n²)"
        assert estimate_complexity(*data["MergeSort"]).best_model == "O(n log n)"
        assert estimate_complexity(*data["HeapSort"]).best_model == "O(n log n)"

    def test_insertion_sort_linear_on_sorted(self):
        results = Benchmark([InsertionSort], [100, 200, 400], generator=SortedInput(), repeats=1).run()
        sizes, values = series(results, "comparisons")["InsertionSort"]
        assert estimate_complexity(sizes, values).best_model == "O(n)"

    def test_series_sorted_by_size(self):
        r = [BenchmarkResult("A", "random", n, np.array([n / 1000]), n, 0) for n in (30, 10, 20)]
        sizes, values = series(r, "comparisons")["A"]
        assert sizes.tolist() == [10, 20, 30]
        assert series(r, "time")["A"][1].tolist() == pytest.approx([0.01, 0.02, 0.03])


class TestRunRepository:
    def test_save_and_filter(self):
        db = Database()
        SqlProgressRepository(db).create_student("Даніїл")
        repo = AlgorithmRunRepository(db)
        results = Benchmark([BubbleSort, QuickSort], [10, 20], generator=RandomInput(), repeats=2).run()
        assert repo.save(results, student_name="Даніїл") == 4
        repo.save(results[:1])  # без студента
        assert repo.count() == 5
        assert len(repo.history(algorithm="QuickSort")) == 2
        assert len(repo.history(student_name="Даніїл")) == 4
        assert len(repo.history(input_kind="sorted")) == 0
        run = repo.history(algorithm="BubbleSort")[0]
        assert run.size == 10 and run.mean_time == pytest.approx(results[0].mean_time)
        repo.clear()
        assert repo.count() == 0
