"""Interface classes for the LWW-Element-Graph implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import Iterable, Mapping, Optional, Protocol, Set, TypeVar, Union

from crdt.lww_graph.edge import Edge
from crdt.lww_graph.operation import LWWGraphOperation

T = TypeVar("T")


class LWWGraph(Protocol[T]):
    """Interface for LWW-element-graph implementations.

    - Besides the interface contract, note that in case of conflicting add and
    remove (with the same timestamp) of an edge or vertex, the remove operation
    takes precedence.

    - Also note that vertex deletions remove all edges that contain the vertex.
    Finally, adding a previously (in causality time) removed vertex should NOT
    restore the previously cascaded edge deletions.
    """

    @property
    @abstractmethod
    def vertices(self) -> Iterable[T]:
        ...

    @property
    @abstractmethod
    def edges(self) -> Iterable[Edge[T]]:
        ...

    @property
    @abstractmethod
    def components(self) -> Iterable[Mapping[T, Set[T]]]:
        """Return an iterable of all graph components. Each component is
        represented by a mapping from each vertex to its incident edges."""

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        ...

    def add_vertex(self, vertex: T, ts: Optional[int] = None) -> LWWGraphOperation[T]:
        ...

    def add_edge(self, edge: Edge[T], ts: Optional[int] = None) -> LWWGraphOperation[T]:
        ...

    def remove_vertex(
        self, vertex: T, ts: Optional[int] = None
    ) -> LWWGraphOperation[T]:
        ...

    def remove_edge(
        self, edge: Edge[T], ts: Optional[int] = None
    ) -> LWWGraphOperation[T]:
        ...
