"""Interface classes for the LWW-Element-Graph implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import Protocol, TypeVar, Union

from crdt.lww_graph.edge import Edge
from crdt.lww_graph.operation import LWWGraphOperation
from crdt.lww_set.interface import LWWSet

T = TypeVar("T")


class LWWGraph(Protocol[T]):
    @abstractmethod
    @property
    def vertices(self) -> LWWSet[T]:
        ...

    @abstractmethod
    @property
    def edges(self) -> LWWSet[Edge[T]]:
        ...

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        ...

    def add_vertex(self, item: T) -> LWWGraphOperation[T]:
        ...

    def add_edge(self, item: Edge[T]) -> LWWGraphOperation[T]:
        ...

    def remove_vertex(self, item: T) -> LWWGraphOperation[T]:
        ...

    def remove_edge(self, item: Edge[T]) -> LWWGraphOperation[T]:
        ...
