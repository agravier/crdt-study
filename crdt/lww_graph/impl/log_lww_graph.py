"""Simple LWW-element-graph implementation based on append-only LWW-element-log
"""
from typing import Iterable, Set, Union

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
        self._vertices: LogLWWSet = LogLWWSet(clock=clock)
        self._edges: LogLWWSet = LogLWWSet(clock=clock)

    @property
    def vertices(self) -> Iterable[T]:
        """Return the LWW-element-set backing the set of vertices that defines
        this graph"""
        return self._vertices.elements

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        # We don't use LogLWWSet.__contains__ as an optimization
        vertices = set(self._vertices.elements)
        if isinstance(item, Edge):
            a, b = item.vertices
            return a in vertices and b in vertices and item in self._edges
        return item in vertices

    @property
    def edges(self) -> Iterable[Edge[T]]:
        """Return the LWW-element-set backing the set of edges that defines
        this graph, without the edges with an invalid vertex."""
        vertices: Set[T] = set(self._vertices.elements)
        for edge in self._edges.elements:
            a, b = edge.vertices
            if a in vertices and b in vertices:
                yield edge

    def add_vertex(self, vertex: T) -> LWWGraphOperation[T]:
        set_op = self._vertices.add(item=vertex)
        return LWWGraphOperation[T](op="add_v", arg=vertex, ts=set_op.ts)

    def add_edge(self, edge: Edge[T]) -> LWWGraphOperation[T]:
        set_op = self._edges.add(item=edge)
        return LWWGraphOperation[T](op="add_e", arg=edge, ts=set_op.ts)

    def remove_vertex(self, vertex: T) -> LWWGraphOperation[T]:
        set_op = self._vertices.remove(item=vertex)
        return LWWGraphOperation[T](op="del_v", arg=vertex, ts=set_op.ts)

    def remove_edge(self, edge: Edge[T]) -> LWWGraphOperation[T]:
        set_op = self._edges.remove(item=edge)
        return LWWGraphOperation[T](op="del_e", arg=edge, ts=set_op.ts)
