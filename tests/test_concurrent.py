import multiprocessing as mp
import sys
import threading

import pytest

from src.data_structures.concurrent import AtomicReference, LockFreeStack, LockFreeQueue, SPSCRingBuffer
from src.data_structures.concurrent.demo import hammer_stack, hammer_queue, produce_range, ring_buffer_between_processes


@pytest.fixture
def frequent_switching():
    """Часте перемикання потоків, щоб вони справді конкурували між собою."""
    old = sys.getswitchinterval()
    sys.setswitchinterval(1e-4)
    yield
    sys.setswitchinterval(old)


def run_threads(targets, timeout=20):
    threads = [threading.Thread(target=t) for t in targets]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout)
    assert not any(t.is_alive() for t in threads), "потоки не завершились - можливе зависання"


class TestAtomicReference:
    def test_compare_and_set(self):
        a, b = object(), object()
        ref = AtomicReference(a)
        assert ref.compare_and_set(a, b) and ref.get() is b
        assert not ref.compare_and_set(a, a) and ref.get() is b

    def test_compares_identity_not_equality(self):
        ref = AtomicReference([1])
        assert not ref.compare_and_set([1], [2])

    def test_concurrent_counter(self, frequent_switching):
        counter = AtomicReference(0)

        def inc():
            for _ in range(2000):
                while True:
                    v = counter.get()
                    if counter.compare_and_set(v, v + 1):
                        break
        run_threads([inc] * 4)
        assert counter.get() == 8000


class TestLockFreeStack:
    def test_lifo(self):
        s = LockFreeStack()
        for v in [1, 2, 3]:
            s.push(v)
        assert s.get_all() == [3, 2, 1]
        assert s.peek() == 3 and s.size == 3 and s.find(1) == 2
        assert [s.pop(), s.pop(), s.pop(), s.pop()] == [3, 2, 1, None]
        assert s.is_empty()

    def test_base_interface(self):
        s = LockFreeStack()
        s.insert("a")
        assert s.delete() == "a" and s.find("a") == -1

    def test_no_lost_items_under_contention(self, frequent_switching):
        stack, ok = hammer_stack(threads=6, per_thread=2000)
        assert ok
        assert stack.is_empty()


class TestLockFreeQueue:
    def test_fifo(self):
        q = LockFreeQueue()
        for v in [1, 2, 3]:
            q.enqueue(v)
        assert q.get_all() == [1, 2, 3] and q.peek() == 1 and q.size == 3
        assert [q.dequeue(), q.dequeue(), q.dequeue(), q.dequeue()] == [1, 2, 3, None]
        q.insert(9)
        assert q.find(9) == 0 and q.delete() == 9 and q.is_empty()

    def test_mpmc_no_lost_items(self, frequent_switching):
        assert hammer_queue(producers=3, consumers=3, per_producer=2000)

    def test_order_per_producer_kept(self, frequent_switching):
        q = LockFreeQueue()
        out = []

        def producer(tag):
            def run():
                for i in range(1500):
                    q.enqueue((tag, i))
            return run
        run_threads([producer("a"), producer("b")])
        while (item := q.dequeue()) is not None:
            out.append(item)
        for tag in "ab":
            seq = [i for t, i in out if t == tag]
            assert seq == list(range(1500))


class TestSPSCRingBuffer:
    def test_put_get_wraps_around(self):
        with SPSCRingBuffer(capacity=3) as rb:
            for round_ in range(5):
                assert rb.try_put(round_ * 10) and rb.try_put(round_ * 10 + 1)
                assert rb.try_get() == round_ * 10
                assert rb.try_get() == round_ * 10 + 1
            assert rb.try_get() is None and rb.is_empty()

    def test_full(self):
        with SPSCRingBuffer(capacity=2) as rb:
            assert rb.try_put(1) and rb.try_put(2)
            assert rb.is_full() and not rb.try_put(3)
            assert len(rb) == 2

    def test_invalid_capacity(self):
        with pytest.raises(ValueError):
            SPSCRingBuffer(capacity=0)

    def test_attach_by_name(self):
        with SPSCRingBuffer(capacity=4) as owner:
            other = SPSCRingBuffer(capacity=4, name=owner.name)
            other.try_put(42)
            assert owner.try_get() == 42
            other.close()

    def test_between_processes(self):
        ok, _ = ring_buffer_between_processes(count=20_000, capacity=64)
        assert ok

    def test_child_process_exit_code(self):
        ctx = mp.get_context("spawn")
        with SPSCRingBuffer(capacity=8) as rb:
            p = ctx.Process(target=produce_range, args=(rb, 5))
            p.start()
            got = []
            while len(got) < 5:
                v = rb.try_get()
                if v is not None:
                    got.append(v)
            p.join(10)
            assert p.exitcode == 0 and got == [0, 1, 2, 3, 4]
