"""Simple LWW-element-graph implementation based on append-only LWW-element-log
"""
from collections import defaultdict
from typing import DefaultDict, Dict, Final, Iterable, List, Optional, Set, Tuple, Union

from crdt.clock.interface import Clock
from crdt.functools.typing import assert_never
from crdt.lww_graph.edge import BaseEdge, Edge
from crdt.lww_graph.interface import LWWGraph, T
from crdt.lww_graph.operation import LWWGraphOperation, LWWGraphOpName

# When sorting the operations log, we use the following ordering between
# operations to break down timestamp ties.
OP_ORDER: Final[Dict[LWWGraphOpName, int]] = {
    "del_e": 1,
    "del_v": 2,
    "add_v": 3,
    "add_e": 4,
}


def _process_add_edge_operation(
    op: LWWGraphOperation,
    last_operations: Dict[LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]],
    edges: Set[BaseEdge[T]],
) -> None:
    try:
        add_a_ts = last_operations["add_v"][op.arg.a]
        add_b_ts = last_operations["add_v"][op.arg.b]
    except KeyError:
        # The edge can't be added because one of the vertices was never created
        pass
    else:
        a_is_deleted = add_a_ts <= last_operations["del_v"].get(op.arg.a, add_a_ts - 1)
        b_is_deleted = add_b_ts <= last_operations["del_v"].get(op.arg.b, add_b_ts - 1)
        if (
            not (a_is_deleted or b_is_deleted)
            and last_operations["del_e"].get(op.arg, op.ts - 1) < op.ts
        ):
            # Any vertex deletion precedes its last addition, so the edge can exist
            edges.add(op.arg)


def _process_delete_edge_operation(
    op: LWWGraphOperation, edges: Set[BaseEdge[T]]
) -> None:
    try:
        edges.remove(op.arg)
    except KeyError:
        pass


def _process_add_vertex_operation(
    op: LWWGraphOperation,
    last_operations: Dict[LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]],
    vertices: Set[T],
) -> None:
    if last_operations["del_v"].get(op.arg, op.ts - 1) < op.ts:
        vertices.add(op.arg)  # type: ignore


def _process_delete_vertex_operation(
    op: LWWGraphOperation,
    last_operations: Dict[LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]],
    vertices: Set[T],
    edges: Set[BaseEdge[T]],
) -> None:
    try:
        vertices.remove(op.arg)  # type: ignore
    except KeyError:
        # The vertex is not here at the currently processed timestamp, nothing to do
        pass
    else:
        # The vertex existed at the deletion time; we must search for edges that contained it.
        edges_for_deletion: Set[BaseEdge[T]] = set()
        edge: BaseEdge[T]
        for edge in edges:
            if op.arg in edge:
                # `edge` contained our deleted vertex, we nee to delete it too.
                edges_for_deletion.add(edge)
                last_operations["del_e"][edge] = op.ts
        edges.difference_update(edges_for_deletion)


class LogLWWGraph(LWWGraph[T]):
    """Simplistic LWW-element-graph local process that records operations as
    they come to an in-memory log. There is no garbage collection, no log
    compression, no persistence to disk, etc."""

    def __init__(self, clock: Clock) -> None:
        self.clock = clock
        self._oplog: List[LWWGraphOperation] = []

    @property
    def _current_state(self) -> Tuple[Set[T], Set[BaseEdge[T]]]:
        """Iterate over the operations log to determine which vertices and
        edges are currently present."""
        # Mapping: operation (add/del edge/vertex) -> edge/vertex -> last timestamp
        last_op: DefaultDict[
            LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]
        ] = defaultdict(dict)
        # Known vertices and edges at current processing point
        vertices: Set[T] = set()
        edges: Set[BaseEdge[T]] = set()
        # Go through the sorted log
        for op in sorted(self._oplog, key=lambda o: (o.ts, OP_ORDER[o.op])):
            last_op[op.op][op.arg] = op.ts
            if op.op == "add_e":
                _process_add_edge_operation(op=op, last_operations=last_op, edges=edges)
            elif op.op == "del_e":
                _process_delete_edge_operation(op=op, edges=edges)
            elif op.op == "add_v":
                _process_add_vertex_operation(
                    op=op, last_operations=last_op, vertices=vertices
                )
            elif op.op == "del_v":
                _process_delete_vertex_operation(
                    op=op, last_operations=last_op, vertices=vertices, edges=edges
                )
            else:
                assert_never(op.op)
        return vertices, edges

    @property
    def vertices(self) -> Iterable[T]:
        """Return the set of vertices that defines this graph"""
        return self._current_state[0]

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        if isinstance(item, Edge):
            return item in self._current_state[1]
        return item in self._current_state[0]

    @property
    def edges(self) -> Iterable[BaseEdge[T]]:
        """Return the set of edges that defines this graph, without the edges
        with an invalid vertex."""
        return self._current_state[1]

    def _record_op(
        self, op: LWWGraphOpName, arg: Union[T, Edge[T]], ts: Optional[int]
    ) -> LWWGraphOperation[T]:
        ts = ts if ts is not None else self.clock.nanoseconds
        operation = LWWGraphOperation[T](op=op, arg=arg, ts=ts)
        self._oplog.append(operation)
        return operation

    def add_vertex(self, vertex: T, ts: Optional[int] = None) -> LWWGraphOperation[T]:
        return self._record_op("add_v", vertex, ts)

    def add_edge(self, edge: Edge[T], ts: Optional[int] = None) -> LWWGraphOperation[T]:
        return self._record_op("add_e", edge, ts)

    def remove_vertex(
        self, vertex: T, ts: Optional[int] = None
    ) -> LWWGraphOperation[T]:
        return self._record_op("del_v", vertex, ts)

    def remove_edge(
        self, edge: Edge[T], ts: Optional[int] = None
    ) -> LWWGraphOperation[T]:
        return self._record_op("del_e", edge, ts)
