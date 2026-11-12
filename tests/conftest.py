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
