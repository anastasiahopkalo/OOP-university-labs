"""Набір вправ для вкладки «Вправи»."""
from typing import List

from src.core.exercise import CodeExercise, TestCase


def default_exercises() -> List[CodeExercise]:
    return [
        CodeExercise(
            "Максимальний елемент",
            "Поверніть найбільший елемент списку <b>без</b> вбудованої функції <code>max()</code>. "
            "Список не порожній.",
            "def solve(numbers):\n    # Ваш код тут\n    pass\n",
            [
                TestCase(([3, 1, 4, 1, 5],), 5),
                TestCase(([-7, -2, -9],), -2),
                TestCase(([42],), 42),
                TestCase(([5, 5, 5, 5],), 5),
                TestCase((list(range(1000)),), 999),
            ],
            difficulty="Легка",
            hint="Запам'ятайте перший елемент і пройдіться циклом по решті, оновлюючи найбільший.",
        ),
        CodeExercise(
            "Розворот списку",
            "Поверніть новий список з елементами у зворотному порядку. "
            "Не використовуйте <code>reversed()</code> і зрізи <code>[::-1]</code>.",
            "def solve(items):\n    # Ваш код тут\n    pass\n",
            [
                TestCase(([1, 2, 3],), [3, 2, 1]),
                TestCase(([],), []),
                TestCase((["a"],), ["a"]),
                TestCase(([1, 2, 2, 3],), [3, 2, 2, 1]),
            ],
            difficulty="Легка",
            hint="Можна покласти всі елементи в стек і дістати їх - вони вийдуть у зворотному порядку.",
        ),
        CodeExercise(
            "Бінарний пошук",
            "Список <code>arr</code> відсортований за зростанням. Поверніть індекс <code>target</code> "
            "або <code>-1</code>, якщо його немає. Складність має бути O(log n).",
            "def solve(arr, target):\n    # Ваш код тут\n    pass\n",
            [
                TestCase(([1, 3, 5, 7, 9], 7), 3),
                TestCase(([1, 3, 5, 7, 9], 1), 0),
                TestCase(([1, 3, 5, 7, 9], 9), 4),
                TestCase(([1, 3, 5, 7, 9], 4), -1),
                TestCase(([], 1), -1),
                TestCase((list(range(0, 200000, 2)), 199998), 99999),
            ],
            difficulty="Середня",
            hint="Тримайте межі low і high, порівнюйте target із серединою і відкидайте половину.",
        ),
        CodeExercise(
            "Сортування бульбашкою",
            "Реалізуйте сортування бульбашкою і поверніть відсортований список. "
            "Вбудовані <code>sorted()</code> і <code>list.sort()</code> використовувати не можна.",
            "def solve(numbers):\n    arr = list(numbers)\n    # Ваш код тут\n    return arr\n",
            [
                TestCase(([5, 1, 4, 2, 8],), [1, 2, 4, 5, 8]),
                TestCase(([],), []),
                TestCase(([1],), [1]),
                TestCase(([3, 3, 1, 1],), [1, 1, 3, 3]),
                TestCase(([-1, -5, 0, 2],), [-5, -1, 0, 2]),
            ],
            difficulty="Середня",
            hint="Два вкладені цикли: на кожному проході найбільший елемент «спливає» в кінець.",
        ),
        CodeExercise(
            "Правильні дужки",
            "Рядок містить лише символи <code>()[]{}</code>. Поверніть <code>True</code>, якщо дужки "
            "розставлені правильно, інакше <code>False</code>.",
            "def solve(s):\n    # Ваш код тут\n    pass\n",
            [
                TestCase(("()",), True),
                TestCase(("()[]{}",), True),
                TestCase(("([{}])",), True),
                TestCase(("(]",), False),
                TestCase(("([)]",), False),
                TestCase(("(((",), False),
                TestCase(("",), True),
            ],
            difficulty="Середня",
            hint="Класична задача на стек: відкриваючу дужку кладіть у стек, закриваюча має "
                 "відповідати верхній.",
        ),
        CodeExercise(
            "Злиття відсортованих списків",
            "Списки <code>a</code> і <code>b</code> відсортовані. Поверніть один відсортований список "
            "за O(n + m) - так само, як у кроці merge сортування злиттям.",
            "def solve(a, b):\n    # Ваш код тут\n    pass\n",
            [
                TestCase(([1, 3, 5], [2, 4, 6]), [1, 2, 3, 4, 5, 6]),
                TestCase(([], [1, 2]), [1, 2]),
                TestCase(([1, 1], [1]), [1, 1, 1]),
                TestCase(([5, 6], [1, 2]), [1, 2, 5, 6]),
            ],
            difficulty="Середня",
            hint="Два вказівники i та j: щоразу беріть менший з a[i] і b[j].",
        ),
        CodeExercise(
            "Компоненти зв'язності",
            "Неорієнтований граф має вершини <code>0..n-1</code> і список ребер <code>edges</code> "
            "(пари <code>(u, v)</code>). Поверніть кількість компонент зв'язності.",
            "def solve(n, edges):\n    # Ваш код тут\n    pass\n",
            [
                TestCase((5, [(0, 1), (1, 2), (3, 4)]), 2),
                TestCase((3, []), 3),
                TestCase((4, [(0, 1), (1, 2), (2, 3), (3, 0)]), 1),
                TestCase((1, []), 1),
                TestCase((6, [(0, 1), (2, 3), (4, 5)]), 3),
            ],
            difficulty="Складна",
            hint="Побудуйте списки суміжності й запускайте BFS або DFS з кожної ще не відвіданої вершини.",
        ),
    ]
