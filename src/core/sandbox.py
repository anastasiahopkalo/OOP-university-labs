"""Запуск коду користувача в окремому процесі з обмеженням часу.

Окремий процес потрібен, щоб нескінченний цикл чи падіння в рішенні
не зупинили GUI: якщо час вийшов, процес просто завершується.
"""
import copy
import multiprocessing as mp
import time
from dataclasses import dataclass, field
from typing import Any, List, Optional, Sequence

# spawn - безпечний з Qt і однаково працює на Linux, Windows і macOS
_CONTEXT = mp.get_context("spawn")


@dataclass
class CaseOutcome:
    status: str          # "ok", "error" або "timeout"
    value: Any = None    # результат функції або текст помилки
    elapsed: float = 0.0


@dataclass
class SandboxReport:
    outcomes: List[CaseOutcome] = field(default_factory=list)
    error: Optional[str] = None   # помилка компіляції / відсутня функція


def _safe_send(conn, message):
    try:
        conn.send(message)
    except Exception:  # результат, який не можна передати між процесами
        kind, value, elapsed = message[1], message[2], message[3]
        conn.send(("case", kind, repr(value), elapsed))


def _worker(code: str, function_name: str, cases: Sequence[tuple], conn):
    namespace = {"__name__": "__solution__"}
    try:
        exec(compile(code, "<рішення>", "exec"), namespace)
    except Exception as error:
        conn.send(("fatal", f"{type(error).__name__}: {error}"))
        return
    func = namespace.get(function_name)
    if not callable(func):
        conn.send(("fatal", f"Не знайдено функцію {function_name}()"))
        return

    for args in cases:
        start = time.perf_counter()
        try:
            value = func(*copy.deepcopy(args))
            _safe_send(conn, ("case", "ok", value, time.perf_counter() - start))
        except Exception as error:
            conn.send(("case", "error", f"{type(error).__name__}: {error}", time.perf_counter() - start))
    conn.send(("finished",))


def run_code(code: str, function_name: str, cases: Sequence[tuple], timeout: float = 3.0) -> SandboxReport:
    """Виконує function_name(*args) для кожного набору args з cases.

    timeout - загальний ліміт на всі тести (без часу запуску процесу).
    """
    report = SandboxReport()
    parent_conn, child_conn = _CONTEXT.Pipe(duplex=False)
    process = _CONTEXT.Process(target=_worker, args=(code, function_name, list(cases), child_conn),
                               daemon=True)
    process.start()
    child_conn.close()

    deadline = None
    try:
        while len(report.outcomes) < len(cases):
            # Перший тест чекаємо довше: процесу треба запуститися
            wait = 10.0 if deadline is None else max(0.0, deadline - time.monotonic())
            if not parent_conn.poll(wait):
                break
            try:
                message = parent_conn.recv()
            except EOFError:
                report.error = report.error or "Процес рішення несподівано завершився"
                break
            if deadline is None:
                deadline = time.monotonic() + timeout
            if message[0] == "fatal":
                report.error = message[1]
                break
            if message[0] == "finished":
                break
            _, status, value, elapsed = message
            report.outcomes.append(CaseOutcome(status, value, elapsed))
    finally:
        if process.is_alive():
            process.terminate()
        process.join(1)
        parent_conn.close()

    if report.error is None:
        while len(report.outcomes) < len(cases):
            report.outcomes.append(CaseOutcome("timeout", f"Перевищено ліміт часу {timeout:g} с", timeout))
    return report
