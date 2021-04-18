"""Interface classes for the LWW-Element-Set implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import Protocol, TypeVar

T = TypeVar("T", contravariant=True)


class MutableLWWSet(Protocol[T]):
    def __contains__(self, item: T) -> bool:
        ...

    def add(self, item: T) -> None:
        ...

    def remove(self, item: T) -> None:
        ...


class ImmutableLWWSet(Protocol[T]):
    def __contains__(self, item: T) -> bool:
        ...

    def add(self, item: T) -> ImmutableLWWSet[T]:
        ...

    def remove(self, item: T) -> ImmutableLWWSet[T]:
        ...
