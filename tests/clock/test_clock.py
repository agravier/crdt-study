"""Black-box unit tests of Clock implementations"""
import time
from typing import List

import pytest

from crdt.clock.impl.mocktime import MockMonotonicClock
from crdt.clock.impl.realtime import MonotonicRealTimeClock
from crdt.clock.interface import Clock


def make_new_instance_of_each_impl() -> List[Clock]:
    """Make a new instance of each implementation of the Clock interface, with
    a reference time of 0."""
    return [
        MockMonotonicClock(0),
        MonotonicRealTimeClock(0),
    ]


@pytest.mark.parametrize("clock", make_new_instance_of_each_impl())
def test_correctness_via_interface(
    clock: Clock,
) -> None:
    """Run simple correctness tests on each Clock implementation."""
    t1 = clock.nanoseconds
    assert t1 >= 0
    time.sleep(0.001)
    t2 = clock.nanoseconds
    assert t2 > t1
