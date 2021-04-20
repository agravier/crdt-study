"""Interface classes for the LWW-Element-Set implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import Iterable, Protocol, TypeVar

from crdt.clock.interface import Clock
from crdt.lww_set.operation import LWWSetOperation

T = TypeVar("T")


class LWWSet(Protocol[T]):
    clock: Clock

    @abstractmethod
    @property
    def elements(self) -> Iterable[T]:
        ...

    def __contains__(self, item: T) -> bool:
        ...

    def add(self, item: T) -> LWWSetOperation[T]:
        ...

    def remove(self, item: T) -> LWWSetOperation[T]:
        ...
