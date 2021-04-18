"""Interface classes for the LWW-Element-Graph implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, Set, TypeVar, Union

from crdt.lww_graph.edge import Edge

T = TypeVar("T")


class MutableLWWGraph(Protocol[T]):
    @abstractmethod
    @property
    def vertices(self) -> Set[T]:
        ...

    @abstractmethod
    @property
    def edges(self) -> Set[Edge[T]]:
        ...

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        ...

    def add_vertex(self, item: T) -> None:
        ...

    def add_edge(self, item: Edge[T]) -> None:
        ...

    def remove_vertex(self, item: T) -> None:
        ...

    def remove_edge(self, item: Edge[T]) -> None:
        ...


class ImmutableLWWGraph(Protocol[T]):
    @abstractmethod
    @property
    def vertices(self) -> Set[T]:
        ...

    @abstractmethod
    @property
    def edges(self) -> Set[Edge[T]]:
        ...

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        ...

    def add_vertex(self, item: T) -> ImmutableLWWGraph[T]:
        ...

    def add_edge(self, item: Edge[T]) -> ImmutableLWWGraph[T]:
        ...

    def remove_vertex(self, item: T) -> ImmutableLWWGraph[T]:
        ...

    def remove_edge(self, item: Edge[T]) -> ImmutableLWWGraph[T]:
        ...
