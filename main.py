"""
CodeLearn Studio - Main Entry Point

    python main.py            # графічний інтерфейс (ЛР2)
    python main.py --console  # консольна перевірка компонентів (ЛР1)
    python main.py --concurrency  # демо неблокуючих структур даних
"""

import sys

from src import (
    QuickSort, MergeSort, BubbleSort,
    LinkedList, Stack, Queue,
    Exercise, ProgressTracker
)


def console_demo():
    print("=" * 70)
    print("CODELEARN STUDIO - Component Test")
    print("=" * 70)

    # Test data
    test_data = [64, 34, 25, 12, 22, 11, 90, 88]

    # ===== TEST 1: ALGORITHMS =====
    print("\n1. SORTING ALGORITHMS")
    print("-" * 70)

    algorithms = [QuickSort(), MergeSort(), BubbleSort()]

    for algo in algorithms:
        result = algo.execute(test_data.copy())
        stats = algo.get_statistics()
        print(f"{algo.name:15} | Result: {result}")
        print(f"{'':15} | Stats: {stats}\n")

    # ===== TEST 2: DATA STRUCTURES =====
    print("2. DATA STRUCTURES")
    print("-" * 70)

    # LinkedList
    print("LinkedList:")
    ll = LinkedList()
    for num in [5, 10, 3, 8]:
        ll.insert(num)
    print(f"  Data: {ll.get_all()}")
    print(f"  Size: {ll.size}")
    print(f"  Find 10: Position {ll.find(10)}\n")

    # Stack
    print("Stack (LIFO):")
    stack = Stack()
    for num in [1, 2, 3]:
        stack.push(num)
    print(f"  Pushed: 1, 2, 3")
    print(f"  Popped: {stack.pop()}, {stack.pop()}, {stack.pop()}\n")

    # Queue
    print("Queue (FIFO):")
    queue = Queue()
    for num in [1, 2, 3]:
        queue.enqueue(num)
    print(f"  Enqueued: 1, 2, 3")
    print(f"  Dequeued: {queue.dequeue()}, {queue.dequeue()}, {queue.dequeue()}\n")

    # ===== TEST 3: EXERCISES =====
    print("3. EXERCISES & PROGRESS")
    print("-" * 70)

    tracker = ProgressTracker("John Doe")

    exercises = [
        Exercise("Sort with QuickSort", QuickSort(), test_data.copy()),
        Exercise("Sort with MergeSort", MergeSort(), test_data.copy()),
        Exercise("Sort with BubbleSort", BubbleSort(), test_data.copy()),
    ]

    for exercise in exercises:
        result = exercise.execute()
        tracker.record_attempt(exercise.title, result)
        print(f"{exercise.title:30} | {result.message} ({result.score}/100)")

    print("\nStudent Progress:")
    stats = tracker.get_statistics()
    for key, value in stats.items():
        print(f"  {key:20}: {value}")

    print("\n" + "=" * 70)
    print("✓ All components tested successfully!")
    print("=" * 70)


def run_gui():
    from PyQt5.QtWidgets import QApplication
    from src.gui.main_window import MainWindow

    app = QApplication(sys.argv)
    # Від назв залежить папка, де зберігається прогрес (progress.json)
    app.setOrganizationName("CodeLearn")
    app.setApplicationName("CodeLearnStudio")
    window = MainWindow()
    window.show()
    return app.exec_()


if __name__ == "__main__":
    if "--console" in sys.argv:
        console_demo()
    elif "--concurrency" in sys.argv:
        from src.data_structures.concurrent.demo import main as concurrency_demo
        concurrency_demo()
    else:
        sys.exit(run_gui())