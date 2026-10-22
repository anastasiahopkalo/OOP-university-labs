import pytest

from src.core.exercise import CodeExercise, TestCase, Exercise, BaseExercise
from src.core.exercise_catalog import default_exercises
from src.core.sandbox import run_code
from src.algorithms.sorting.quick_sort import QuickSort

# Еталонні рішення для кожної вправи з каталогу
SOLUTIONS = {
    "Максимальний елемент": """
def solve(numbers):
    best = numbers[0]
    for x in numbers[1:]:
        if x > best:
            best = x
    return best
""",
    "Розворот списку": """
def solve(items):
    result = []
    for x in items:
        result.insert(0, x)
    return result
""",
    "Бінарний пошук": """
def solve(arr, target):
    low, high = 0, len(arr) - 1
    while low <= high:
        mid = (low + high) // 2
        if arr[mid] == target:
            return mid
        if arr[mid] < target:
            low = mid + 1
        else:
            high = mid - 1
    return -1
""",
    "Сортування бульбашкою": """
def solve(numbers):
    arr = list(numbers)
    for i in range(len(arr)):
        for j in range(len(arr) - i - 1):
            if arr[j] > arr[j + 1]:
                arr[j], arr[j + 1] = arr[j + 1], arr[j]
    return arr
""",
    "Правильні дужки": """
def solve(s):
    pairs = {')': '(', ']': '[', '}': '{'}
    stack = []
    for ch in s:
        if ch in pairs:
            if not stack or stack.pop() != pairs[ch]:
                return False
        else:
            stack.append(ch)
    return not stack
""",
    "Злиття відсортованих списків": """
def solve(a, b):
    i = j = 0
    out = []
    while i < len(a) and j < len(b):
        if a[i] <= b[j]:
            out.append(a[i]); i += 1
        else:
            out.append(b[j]); j += 1
    return out + a[i:] + b[j:]
""",
    "Компоненти зв'язності": """
def solve(n, edges):
    adj = {v: [] for v in range(n)}
    for u, v in edges:
        adj[u].append(v); adj[v].append(u)
    seen, count = set(), 0
    for s in range(n):
        if s in seen:
            continue
        count += 1
        stack = [s]
        while stack:
            v = stack.pop()
            if v not in seen:
                seen.add(v)
                stack.extend(adj[v])
    return count
""",
}


class TestSandbox:
    def test_runs_function(self):
        report = run_code("def f(a, b):\n    return a + b\n", "f", [(1, 2), (3, 4)])
        assert report.error is None
        assert [o.value for o in report.outcomes] == [3, 7]
        assert all(o.status == "ok" for o in report.outcomes)

    def test_syntax_error(self):
        report = run_code("def f(:\n", "f", [(1,)])
        assert "SyntaxError" in report.error

    def test_missing_function(self):
        report = run_code("x = 1\n", "solve", [(1,)])
        assert "solve" in report.error

    def test_runtime_error_per_case(self):
        report = run_code("def f(x):\n    return 10 // x\n", "f", [(2,), (0,), (5,)])
        assert [o.status for o in report.outcomes] == ["ok", "error", "ok"]
        assert "ZeroDivisionError" in report.outcomes[1].value

    def test_infinite_loop_times_out(self):
        code = "def f(x):\n    if x:\n        while True:\n            pass\n    return 1\n"
        report = run_code(code, "f", [(0,), (1,), (0,)], timeout=0.5)
        assert [o.status for o in report.outcomes] == ["ok", "timeout", "timeout"]

    def test_input_not_shared_between_cases(self):
        code = "def f(lst):\n    lst.append(1)\n    return len(lst)\n"
        data = [0]
        report = run_code(code, "f", [(data,), (data,)])
        assert [o.value for o in report.outcomes] == [2, 2]
        assert data == [0]


class TestCodeExercise:
    @pytest.fixture
    def exercise(self):
        return CodeExercise("Сума", "Поверніть a + b", "def solve(a, b):\n    pass\n",
                            [TestCase((1, 2), 3), TestCase((0, 0), 0), TestCase((-1, 1), 0),
                             TestCase((5, 5), 10)])

    def test_correct_solution(self, exercise):
        result = exercise.execute("def solve(a, b):\n    return a + b\n")
        assert result.passed and result.score == 100
        assert len(result.details) == 4 and all(d.passed for d in result.details)
        assert exercise.attempts == 1

    def test_partial_solution(self, exercise):
        result = exercise.execute("def solve(a, b):\n    return abs(a) + b\n")
        assert not result.passed
        assert result.score == 75
        assert "3 з 4" in result.message

    def test_template_fails(self, exercise):
        result = exercise.execute(exercise.template)
        assert result.score == 0
        assert all(d.actual is None for d in result.details)

    def test_compile_error(self, exercise):
        result = exercise.execute("def solve(:")
        assert result.score == 0 and result.message.startswith("Помилка")

    def test_requires_test_cases(self):
        with pytest.raises(ValueError):
            CodeExercise("x", "x", "x", [])

    def test_hierarchy(self, exercise):
        assert isinstance(exercise, BaseExercise)
        assert isinstance(Exercise("s", QuickSort(), [2, 1]), BaseExercise)


class TestCatalog:
    def test_every_exercise_has_solution(self):
        assert {e.title for e in default_exercises()} == set(SOLUTIONS)

    @pytest.mark.parametrize("exercise", default_exercises(), ids=lambda e: e.title)
    def test_reference_solution_passes(self, exercise):
        result = exercise.execute(SOLUTIONS[exercise.title])
        assert result.passed, [d for d in result.details if not d.passed]

    @pytest.mark.parametrize("exercise", default_exercises(), ids=lambda e: e.title)
    def test_template_does_not_pass(self, exercise):
        assert not exercise.execute(exercise.template).passed

    def test_legacy_exercise_still_works(self):
        result = Exercise("Sort", QuickSort(), [3, 1, 2]).execute()
        assert result.passed and result.score == 100
