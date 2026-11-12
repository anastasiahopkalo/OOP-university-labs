"""Тести графа знань (networkx)."""
import networkx as nx
import pytest

from src.core.analytics import ProgressTracker
from src.core.exercise import ExerciseResult
from src.core.exercise_catalog import default_exercises
from src.core.knowledge_graph import (
    AVAILABLE, LOCKED, MASTERED, KnowledgeGraph, Topic,
)


def tracker_with(*solved, failed=()):
    t = ProgressTracker("x")
    for title in solved:
        t.record_attempt(title, ExerciseResult(True, 100, "", 0.1))
    for title in failed:
        t.record_attempt(title, ExerciseResult(False, 20, "", 0.1))
    return t


@pytest.fixture
def kg():
    return KnowledgeGraph()


def test_default_graph_is_dag_and_covers_exercises(kg):
    assert nx.is_directed_acyclic_graph(kg.graph)
    assert kg.exercise_titles() == {e.title for e in default_exercises()}


def test_topological_order_respects_prerequisites(kg):
    order = kg.topological_order()
    assert order[0] == "arrays"
    for before, after in kg.graph.edges:
        assert order.index(before) < order.index(after)
    assert [t.key for t in kg.topics()] == order


def test_levels(kg):
    levels = kg.levels()
    assert levels[0] == ["arrays"]
    assert set(levels[1]) == {"binary_search", "simple_sorts", "stack_queue"}
    assert sum(len(level) for level in levels) == kg.graph.number_of_nodes()


def test_prerequisites(kg):
    assert kg.prerequisites("dijkstra") == ["graph_traversal", "trees_heaps"]
    assert "arrays" in kg.all_prerequisites("dijkstra")


def test_new_student(kg):
    t = tracker_with()
    statuses = kg.statuses(t)
    assert statuses["arrays"] == AVAILABLE
    assert all(s == LOCKED for k, s in statuses.items() if k != "arrays")
    assert kg.mastered(t) == []
    assert kg.next_recommended(t).key == "arrays"


def test_partial_topic_is_not_mastered(kg):
    t = tracker_with("Максимальний елемент", failed=["Розворот списку"])
    assert kg.statuses(t)["arrays"] == AVAILABLE
    assert kg.topic_progress("arrays", t) == (1, 2)


def test_progression(kg):
    t = tracker_with("Максимальний елемент", "Розворот списку")
    assert kg.mastered(t) == ["arrays"]
    assert set(kg.available(t)) == {"binary_search", "simple_sorts", "stack_queue"}
    assert kg.next_recommended(t).key == "binary_search"

    t = tracker_with("Максимальний елемент", "Розворот списку", "Бінарний пошук")
    # теорія «Дерева і купи» відкривається й не блокує наступні теми
    assert kg.statuses(t)["trees_heaps"] == AVAILABLE
    assert kg.statuses(t)["heap_sort"] == LOCKED  # ще потрібні прості сортування


def test_everything_solved(kg):
    t = tracker_with(*kg.exercise_titles())
    statuses = kg.statuses(t)
    assert LOCKED not in statuses.values()
    assert all(statuses[t_.key] == MASTERED for t_ in kg.topics() if not t_.is_theory)
    recommended = kg.next_recommended(t)
    assert recommended is not None and recommended.is_theory


def test_validation():
    with pytest.raises(ValueError, match="цикл"):
        KnowledgeGraph([Topic("a", "A", "x"), Topic("b", "B", "x")], [("a", "b"), ("b", "a")])
    with pytest.raises(ValueError, match="Невідома"):
        KnowledgeGraph([Topic("a", "A", "x")], [("a", "zzz")])
    empty = KnowledgeGraph([], [])
    assert empty.next_recommended(tracker_with()) is None
