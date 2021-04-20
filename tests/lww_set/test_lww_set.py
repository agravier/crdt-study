from typing import Any, List

import pytest

from crdt.lww_set.impl.log_lww_set import LogLWWSet
from crdt.lww_set.interface import LWWSet


def make_new_instance_of_each_impl() -> List[LWWSet]:
    return [
        LogLWWSet(),
    ]


@pytest.mark.parametrize("lww_set", make_new_instance_of_each_impl())
def test_correctness_via_interface(
    lww_set: LWWSet[int],
) -> None:
    assert len(set(lww_set.elements)) == 0, "New set should be empty"
    lww_set.add(item=1)
    lww_set.add(item=2)
    lww_set.add(item=1)
    lww_set.remove(item=1)
    lww_set.add(item=1)
    lww_set.add(item=2)
    lww_set.remove(item=2)
