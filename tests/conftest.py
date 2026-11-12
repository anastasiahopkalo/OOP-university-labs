"""Спільні фікстури pytest для всіх тестів."""
import pytest

from src.database import Database


@pytest.fixture
def make_db():
    """Фабрика БД: make_db() - у пам'яті, make_db(path) - SQLite-файл.

    Після тесту всі з'єднання закриваються, щоб не було ResourceWarning.
    """
    created = []

    def factory(path=None) -> Database:
        db = Database.from_path(path) if path else Database()
        created.append(db)
        return db

    yield factory
    for db in created:
        db.dispose()


@pytest.fixture(scope="session")
def app():
    """Один QApplication на всю сесію; GUI-тести працюють без дисплея (offscreen)."""
    import os
    os.environ.setdefault("QT_QPA_PLATFORM", "offscreen")
    QtWidgets = pytest.importorskip("PyQt5.QtWidgets")
    return QtWidgets.QApplication.instance() or QtWidgets.QApplication([])


@pytest.fixture
def random_graph():
    """Фабрика випадкових зважених графів: random_graph(seed, n=..., p=..., directed=...)."""
    import networkx as nx
    from src.algorithms.graphs.nx_adapter import from_networkx

    def factory(seed: int, n: int = 12, p: float = 0.25, directed: bool = False, max_weight: int = 9):
        import random
        rng = random.Random(seed)
        g = nx.gnp_random_graph(n, p, seed=seed, directed=directed)
        for u, v in g.edges:
            g.edges[u, v]["weight"] = rng.randint(1, max_weight)
        return from_networkx(g)
    return factory
