# ЛР2 — розподіл задач

Враховано рекомендації викладача: обов'язковий GUI, нові структури даних
(дерева, купи, хеш-таблиці, графи), `.gitignore`, `requirements.txt`,
бонус — non-blocking структури даних.

GUI-бібліотека: **PyQt5** (як у `CODELEARN_PLAN.md`) — багато готових віджетів,
`QPainter` для власної графіки, `matplotlib` вбудовується через `FigureCanvasQTAgg`.

## Частина 1 — Даніїл ✅ (виконано)

| # | Задача | Файли |
|---|--------|-------|
| 1 | `.gitignore`, прибрано `.venv`, `.idea`, `__pycache__`, `.coverage` з репозиторію; тести перенесено в `tests/` | `.gitignore`, `pytest.ini` |
| 2 | `requirements.txt` (PyQt5, matplotlib, pytest) | `requirements.txt` |
| 3 | Кроки алгоритмів для анімації: `kind` + `snapshot`, шаблонний метод `execute()` → `_sort()` | `src/core/algorithm.py`, `src/algorithms/sorting/*` |
| 4 | Нові структури: `BinarySearchTree`, `BinaryHeap`, `HashTable`, `Graph` + тести | `src/data_structures/*`, `tests/test_new_data_structures.py` |
| 5 | Каркас GUI: `MainWindow`, вкладки, меню, світла/темна тема (Ctrl+T), `QSettings` | `src/gui/main_window.py`, `src/gui/styles.py` |
| 6 | Базове полотно `VisualizationCanvas` для всіх візуалізацій | `src/gui/widgets/canvas.py` |
| 7 | Вкладка «Сортування»: 5 алгоритмів, старт/пауза/крок/назад, швидкість, свої дані, журнал кроків | `src/gui/panels/sorting_panel.py`, `src/gui/step_player.py` |
| 8 | Тести GUI (offscreen) і `StepPlayer` | `tests/test_gui.py`, `tests/test_step_player.py` |

## Частина 2 — Анастасія ⏳

| # | Задача | Файли (орієнтовно) |
|---|--------|-------|
| 1 | Вкладка «Структури даних»: вибір структури (BST, купа, хеш-таблиця, стек, черга, зв'язний список), кнопки insert / delete / find, малювання на `VisualizationCanvas` | `src/gui/panels/data_structures_panel.py`, `src/gui/widgets/*_canvas.py` |
| 2 | Алгоритми на графах `BFS`, `DFS`, `Dijkstra`, що записують кроки (як сортування) + тести | `src/algorithms/graphs/*`, `tests/test_graph_algorithms.py` |
| 3 | Вкладка «Графи»: побудова графа (вершини/ребра/ваги), анімація BFS/DFS/Дейкстри через `StepPlayer` | `src/gui/panels/graph_panel.py` |
| 4 | Вкладка «Вправи»: задачі з автоматичною перевіркою на `Exercise`, результати в таблиці | `src/gui/panels/exercise_panel.py`, `src/core/exercise.py` |
| 5 | Вкладка «Прогрес»: `ProgressTracker` + графік matplotlib | `src/gui/panels/dashboard_panel.py` |
| 6 | Бонус: non-blocking структура (lock-free стек/черга на CAS для free-threaded Python 3.13+ або через `multiprocessing`) + демо/тест | `src/data_structures/concurrent/*` |
| 7 | Оновити `README.md` (запуск, скріншоти, розподіл роботи), тести для нових панелей | `README.md`, `tests/` |

## Запуск

```bash
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
python main.py                   # GUI
python main.py --console         # консольна демонстрація ЛР1
pytest                           # тести
```
