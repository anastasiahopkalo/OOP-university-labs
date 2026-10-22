"""Демонстрація неблокуючих структур даних.

    python -m src.data_structures.concurrent.demo

На звичайному CPython потоки чергуються через GIL, а на free-threaded
збірці (Python 3.13t+) вони справді працюють паралельно - тоді
конкуренція і кількість повторних CAS-спроб помітно зростають.
"""
import multiprocessing as mp
import sys
import threading
import time

from src.data_structures.concurrent.lock_free_queue import LockFreeQueue
from src.data_structures.concurrent.lock_free_stack import LockFreeStack
from src.data_structures.concurrent.spsc_ring_buffer import SPSCRingBuffer


def gil_status() -> str:
    is_enabled = getattr(sys, "_is_gil_enabled", None)
    if is_enabled is None:
        return "GIL увімкнено (Python < 3.13)"
    return "GIL увімкнено" if is_enabled() else "free-threaded: GIL вимкнено"


def hammer_stack(threads: int = 8, per_thread: int = 5000):
    """Кожен потік кладе свої числа і забирає стільки ж. Нічого не має загубитися."""
    stack = LockFreeStack()
    popped = [[] for _ in range(threads)]

    def worker(tid):
        for i in range(per_thread):
            stack.push(tid * per_thread + i)
        for _ in range(per_thread):
            value = stack.pop()
            while value is None:  # інший потік міг забрати "наш" елемент - беремо будь-який
                value = stack.pop()
            popped[tid].append(value)

    pool = [threading.Thread(target=worker, args=(t,)) for t in range(threads)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()
    values = sorted(v for part in popped for v in part)
    return stack, values == list(range(threads * per_thread))


def hammer_queue(producers: int = 4, consumers: int = 4, per_producer: int = 5000):
    queue = LockFreeQueue()
    total = producers * per_producer
    received = []
    lock = threading.Lock()  # лише для збирання результатів демо, не для черги

    def produce(pid):
        for i in range(per_producer):
            queue.enqueue(pid * per_producer + i)

    def consume():
        while True:
            value = queue.dequeue()
            with lock:
                if value is not None:
                    received.append(value)
                if len(received) >= total:
                    return
            if value is None:
                time.sleep(0)  # черга тимчасово порожня - поступаємось іншим потокам

    pool = [threading.Thread(target=produce, args=(p,)) for p in range(producers)]
    pool += [threading.Thread(target=consume) for _ in range(consumers)]
    for t in pool:
        t.start()
    for t in pool:
        t.join()
    return sorted(received) == list(range(total))


def produce_range(buffer: SPSCRingBuffer, count: int):
    """Виробник в окремому процесі: записує числа 0..count-1."""
    for value in range(count):
        while not buffer.try_put(value):
            pass  # буфер повний - активне очікування, без блокувань
    buffer.close()


def ring_buffer_between_processes(count: int = 100_000, capacity: int = 256):
    ctx = mp.get_context("spawn")
    with SPSCRingBuffer(capacity) as buffer:
        producer = ctx.Process(target=produce_range, args=(buffer, count))
        start = time.perf_counter()
        producer.start()
        received = 0
        expected = 0
        in_order = True
        while received < count:
            value = buffer.try_get()
            if value is None:
                continue
            in_order &= value == expected
            expected += 1
            received += 1
        producer.join()
        elapsed = time.perf_counter() - start
    return in_order and received == count, elapsed


def main():
    print(f"Python {sys.version.split()[0]} · {gil_status()}\n")

    # З GIL потоки перемикаються раз на 5 мс і майже не заважають один одному.
    # Частіше перемикання імітує справжню паралельність і показує повторні CAS-спроби.
    old_interval = sys.getswitchinterval()
    sys.setswitchinterval(1e-4)
    try:
        run_thread_demos()
    finally:
        sys.setswitchinterval(old_interval)

    ok, elapsed = ring_buffer_between_processes()
    print(f"SPSCRingBuffer: 100 000 чисел між процесами - {'✓ усе по порядку' if ok else '✗ ПОМИЛКА'}; "
          f"{elapsed:.2f} с")


def run_thread_demos():
    start = time.perf_counter()
    stack, ok = hammer_stack()
    print(f"LockFreeStack: 8 потоків × 5000 push/pop - {'✓ нічого не загубилося' if ok else '✗ ПОМИЛКА'}; "
          f"повторних CAS: {stack.retries}; {time.perf_counter() - start:.2f} с")

    start = time.perf_counter()
    ok = hammer_queue()
    print(f"LockFreeQueue: 4 виробники + 4 споживачі × 5000 - {'✓ усе отримано' if ok else '✗ ПОМИЛКА'}; "
          f"{time.perf_counter() - start:.2f} с")


if __name__ == "__main__":
    main()
