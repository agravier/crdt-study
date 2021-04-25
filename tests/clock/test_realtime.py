"""Test the specific stdlib-based clock implementation"""
import time

from crdt.clock.impl.realtime import MonotonicRealTimeClock


def test_realtime_monotonic_clock__normal_operations() -> None:
    """Try sleeping and observing an increase"""
    clock = MonotonicRealTimeClock(0)
    t1 = clock.nanoseconds
    time.sleep(0.001)
    t2 = clock.nanoseconds
    assert t2 - t1 >= 10 ** 9 / 1000


def test_realtime_monotonic_clock__change_reftime() -> None:
    """Try changing the ref time and observing a decrease in relative time"""
    clock = MonotonicRealTimeClock(0)
    t1 = clock.nanoseconds
    clock.zero += 10 ** 10
    t2 = clock.nanoseconds
    assert t2 < t1
