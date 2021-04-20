from typing import Iterable, List, Dict

from crdt.clock.interface import Clock
from crdt.functools.typing import assert_never
from crdt.lww_set.interface import LWWSet, T
from crdt.lww_set.operation import LWWSetOperation


class LogLWWSet(LWWSet[T]):
    def __init__(self, clock: Clock):
        self.clock = clock
        self._oplog: List[LWWSetOperation] = []

    @property
    def elements(self) -> Iterable[T]:
        """Iterate over the operations log to determine which elements are still
        in the set"""
        last_adds: Dict[T, int] = {}
        last_dels: Dict[T, int] = {}
        for op in self._oplog:
            if op.op == "add":
                collection = last_adds
            elif op.op == "del":
                collection = last_dels
            else:
                assert_never(op.op)
            prev_ts = collection.get(op.arg)  # noqa
            if prev_ts is None or op.ts > prev_ts:
                collection[op.arg] = op.ts
        for key, add_ts in last_adds.items():
            del_ts = last_dels.get(key, add_ts-1)
            if del_ts < add_ts:
                yield key

    def __contains__(self, item: T) -> bool:
        return item in set(self.elements)

    def add(self, item: T) -> LWWSetOperation[T]:
        ...

    def remove(self, item: T) -> LWWSetOperation[T]:
        ...
