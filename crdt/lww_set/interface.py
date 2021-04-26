"""Interface classes for the LWW-Element-Set implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import Iterable, Optional, Protocol, TypeVar

from crdt.clock.interface import Clock
from crdt.lww_set.operation import LWWSetOperation

T = TypeVar("T")


class LWWSet(Protocol[T]):
    """Interface for LWW-element-set implementations. Besides the interface
    contract, note that in case of conflicting add and remove (with the same
    timestamp), the remove operation takes precedence."""

    clock: Clock

    @property
    @abstractmethod
    def elements(self) -> Iterable[T]:
        ...

    def __contains__(self, item: T) -> bool:
        ...

    def add(self, item: T, ts: Optional[int] = None) -> LWWSetOperation[T]:
        ...

    def remove(self, item: T, ts: Optional[int] = None) -> LWWSetOperation[T]:
        ...
