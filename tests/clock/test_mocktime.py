"""Test the specific MockTime clock implementation"""
from pytest import raises

from crdt.clock.impl.mocktime import MockMonotonicClock
from crdt.clock.interface import ClockError


def test_mock_monotonic_clock__normal_operations() -> None:
    """Try setting the time, the time step and the next tick and observe
    behaviour"""
    start = 10
    clock = MockMonotonicClock(start)
    step = clock.step_size
    assert clock.next_tick == start + step
    assert clock.nanoseconds == start + step
    clock = MockMonotonicClock(0)
    clock.step_size = 10
    assert clock.next_tick == 10
    assert clock.nanoseconds == 10
    clock.next_tick = 1000
    assert clock.next_tick == 1000
    assert clock.nanoseconds == 1000
    assert clock.next_tick == 1010
    clock.step_size = 0
    assert clock.next_tick == 1000


def test_mock_monotonic_clock__raises_on_negative_step() -> None:
    """Try setting a negative time step and observe a ClockError"""
    clock = MockMonotonicClock(0)
    with raises(ClockError):
        clock.step_size = -1


def test_mock_monotonic_clock__raises_on_backward_next_tick() -> None:
    """Try setting a next tick in the past and observe a ClockError"""
    clock = MockMonotonicClock(10)
    with raises(ClockError):
        clock.next_tick = 9
