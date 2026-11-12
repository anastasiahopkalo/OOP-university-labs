"""Керування підключенням до бази даних (SQLAlchemy engine + сесії)."""
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Union

from sqlalchemy import create_engine, event
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from src.database.models import Base

MEMORY_URL = "sqlite://"


class Database:
    """Обгортка над engine: створює таблиці та видає сесії-транзакції.

    Database("sqlite://")              - БД у пам'яті (для тестів)
    Database.from_path("progress.db")  - SQLite-файл
    """

    def __init__(self, url: str = MEMORY_URL, echo: bool = False):
        self._url = url
        kwargs = {"echo": echo}
        if url in (MEMORY_URL, "sqlite:///:memory:"):
            # Одне з'єднання на всі сесії, інакше кожна сесія бачила б порожню БД
            kwargs.update(connect_args={"check_same_thread": False}, poolclass=StaticPool)
        self._engine: Engine = create_engine(url, **kwargs)
        if url.startswith("sqlite"):
            event.listen(self._engine, "connect", _enable_foreign_keys)
        self._session_factory = sessionmaker(bind=self._engine, expire_on_commit=False)
        Base.metadata.create_all(self._engine)

    @classmethod
    def from_path(cls, path: Union[str, Path]) -> "Database":
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        return cls(f"sqlite:///{path}")

    @property
    def url(self) -> str:
        return self._url

    @property
    def engine(self) -> Engine:
        return self._engine

    @contextmanager
    def session(self) -> Iterator[Session]:
        """Сесія як транзакція: commit при успіху, rollback при винятку."""
        session = self._session_factory()
        try:
            yield session
            session.commit()
        except Exception:
            session.rollback()
            raise
        finally:
            session.close()

    def dispose(self) -> None:
        """Закриває всі з'єднання пулу."""
        self._engine.dispose()

    def __enter__(self) -> "Database":
        return self

    def __exit__(self, *exc) -> None:
        self.dispose()


def _enable_foreign_keys(dbapi_connection, _record) -> None:
    # SQLite за замовчуванням не перевіряє зовнішні ключі
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()
