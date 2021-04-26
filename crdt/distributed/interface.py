"""Client and server interfaces for distributed LWWGraph"""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from typing import Iterable, List, Protocol, TypeVar

from crdt.lww_graph.edge import Edge
from crdt.lww_graph.interface import LWWGraph
from crdt.lww_graph.operation import LWWGraphOperation

T = TypeVar("T")


class LWWGraphClient(Protocol[T]):
    """A client managing a local graph and sporadic communication with a server.
    The server centralizes updates and communicates them back to all client."""

    graph: LWWGraph[T]

    def connect(self, s: LWWGraphServer) -> None:
        """Perform handshake with server"""
        ...

    def update(self, ops: Iterable[LWWGraphOperation[T]]) -> None:
        """Called by the server (or its proxy) to communicate remote operations"""
        ...

    def add_vertex(self, item: T) -> None:
        """Called locally to register an operation"""
        ...

    def add_edge(self, item: Edge[T]) -> None:
        ...

    def remove_vertex(self, item: T) -> None:
        ...

    def remove_edge(self, item: Edge[T]) -> None:
        ...

    def check_connected(self, a: T, b: T) -> bool:
        ...

    def find_path(self, a: T, b: T) -> List[Edge[T]]:
        ...


class LWWGraphServer(Protocol[T]):

    graph: LWWGraph[T]
    clients: List[LWWGraphClient[T]]

    def register_client(self, c: LWWGraphClient) -> None:
        ...

    def update(self, ops: Iterable[LWWGraphOperation[T]]) -> None:
        ...
