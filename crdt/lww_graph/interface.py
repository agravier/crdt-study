"""Interface classes for the LWW-Element-Graph implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import Iterable, Protocol, TypeVar, Union

from crdt.lww_graph.edge import Edge
from crdt.lww_graph.operation import LWWGraphOperation

T = TypeVar("T")


class LWWGraph(Protocol[T]):
    @property
    @abstractmethod
    def vertices(self) -> Iterable[T]:
        ...

    @property
    @abstractmethod
    def edges(self) -> Iterable[Edge[T]]:
        ...

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        ...

    def add_vertex(self, vertex: T) -> LWWGraphOperation[T]:
        ...

    def add_edge(self, edge: Edge[T]) -> LWWGraphOperation[T]:
        ...

    def remove_vertex(self, vertex: T) -> LWWGraphOperation[T]:
        ...

    def remove_edge(self, edge: Edge[T]) -> LWWGraphOperation[T]:
        ...
