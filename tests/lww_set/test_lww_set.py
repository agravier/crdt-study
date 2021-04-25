"""Black-box unit tests of LWWSet implementations"""

from typing import List

import pytest

from crdt.clock.impl.mocktime import MockMonotonicClock
from crdt.lww_set.impl.log_lww_set import LogLWWSet
from crdt.lww_set.interface import LWWSet


def make_new_instance_of_each_impl() -> List[LWWSet]:
    """Make a new empty instance of each implementation of the LWWSet interface,
    backed by a mock clock."""
    return [
        LogLWWSet(clock=MockMonotonicClock(0)),
    ]


@pytest.mark.parametrize("lww_set", make_new_instance_of_each_impl())
def test_correctness_via_interface(
    lww_set: LWWSet[int],
) -> None:
    """Run simple correctness tests on each implementation of LWWSet."""
    assert len(set(lww_set.elements)) == 0, "New set should be empty"
    lww_set.add(item=1)
    assert set(lww_set.elements) == {1}
    lww_set.add(item=2)
    assert set(lww_set.elements) == {1, 2}
    lww_set.add(item=1)
    assert set(lww_set.elements) == {1, 2}
    lww_set.remove(item=1)
    assert set(lww_set.elements) == {2}
    lww_set.remove(item=1)
    assert set(lww_set.elements) == {2}
    lww_set.add(item=1)
    assert set(lww_set.elements) == {1, 2}
    lww_set.add(item=2)
    assert set(lww_set.elements) == {1, 2}
    lww_set.remove(item=2)
    assert set(lww_set.elements) == {1}
    lww_set.remove(item=1)
    assert set(lww_set.elements) == set()
