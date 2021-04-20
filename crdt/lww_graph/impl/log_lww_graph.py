"""Simple-log based LWW-element-graph implementation"""
from crdt.clock.interface import Clock
from crdt.lww_graph.edge import Edge
from crdt.lww_graph.interface import LWWGraph, T
from crdt.lww_graph.operation import LWWGraphOperation
from crdt.lww_set.impl.log_lww_set import LogLWWSet


class LogLWWGraph(LWWGraph[T]):
    """Simplistic LWW-element-graph local process that uses LWW-element-set
    implementations that records operations as they come to an in-memory log.
    There is no garbage collection, no log compression, no persistence to disk,
    etc."""
    def __init__(self, clock: Clock) -> None:
        self.clock = clock
        self._vertices = LogLWWSet(clock=clock)
        self._edges = LogLWWSet(clock=clock)

    @property
    def vertices(self) -> LogLWWSet[T]:
        """Return the LWW-element-set backing the set of vertices that defines
        this graph"""
        return self._vertices

    @property
    def edges(self) -> LogLWWSet[Edge[T]]:
        """Return the LWW-element-set backing the set of edges that defines
        this graph"""
        return self._edges

    def add_vertex(self, item: T) -> LWWGraphOperation[T]:
        ...

    def add_edge(self, item: Edge[T]) -> LWWGraphOperation[T]:
        ...

    def remove_vertex(self, item: T) -> LWWGraphOperation[T]:
        ...

    def remove_edge(self, item: Edge[T]) -> LWWGraphOperation[T]:
        ...
