"""Simple LWW-element-graph implementation based on append-only LWW-element-log
"""
from collections import defaultdict
from dataclasses import dataclass, field
from typing import (
    DefaultDict,
    Dict,
    Final,
    Generic,
    Iterable,
    List,
    Mapping,
    Optional,
    Set,
    Tuple,
    Union,
)

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


@dataclass
class _Changes(Generic[T]):
    vertices_added: List[T] = field(default_factory=list)
    vertices_removed: List[T] = field(default_factory=list)
    edges_added: List[BaseEdge[T]] = field(default_factory=list)
    edges_removed: List[BaseEdge[T]] = field(default_factory=list)


def _process_add_edge_operation(
    op: LWWGraphOperation,
    last_operations: Dict[LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]],
    edges: Set[BaseEdge[T]],
) -> Optional[_Changes[T]]:
    try:
        add_a_ts = last_operations["add_v"][op.arg.a]
        add_b_ts = last_operations["add_v"][op.arg.b]
    except KeyError:
        # The edge can't be added because one of the vertices was never created
        return None
    else:
        a_is_deleted = add_a_ts <= last_operations["del_v"].get(op.arg.a, add_a_ts - 1)
        b_is_deleted = add_b_ts <= last_operations["del_v"].get(op.arg.b, add_b_ts - 1)
        if (
            not (a_is_deleted or b_is_deleted)
            and last_operations["del_e"].get(op.arg, op.ts - 1) < op.ts
        ):
            # Any vertex deletion precedes its last addition, so the edge can exist
            edges.add(op.arg)
            return _Changes(edges_added=[op.arg])
    return None


def _process_delete_edge_operation(
    op: LWWGraphOperation, edges: Set[BaseEdge[T]]
) -> Optional[_Changes[T]]:
    try:
        edges.remove(op.arg)
        return _Changes(edges_removed=[op.arg])
    except KeyError:
        return None


def _process_add_vertex_operation(
    op: LWWGraphOperation[T],
    last_operations: Dict[LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]],
    vertices: Set[T],
) -> Optional[_Changes[T]]:
    vertex: T = op.arg  # type: ignore
    if last_operations["del_v"].get(vertex, op.ts - 1) < op.ts:
        vertices.add(vertex)
        return _Changes(vertices_added=[vertex])
    return None


def _process_delete_vertex_operation(
    op: LWWGraphOperation[T],
    last_operations: Dict[LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]],
    vertices: Set[T],
    edges: Set[BaseEdge[T]],
) -> Optional[_Changes[T]]:
    vertex: T = op.arg  # type: ignore
    try:
        vertices.remove(vertex)
    except KeyError:
        # The vertex is not here at the currently processed timestamp, nothing to do
        return None
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
        return _Changes(
            vertices_removed=[vertex], edges_removed=list(edges_for_deletion)
        )


def _find_index_of_component_with_vertex(
    components: List[Dict[T, Set[T]]], vertex: T
) -> int:
    return next(i for i, c in enumerate(components) if vertex in c)


def _merge_dicts_of_sets(into: Dict[T, Set[T]], other: Dict[T, Set[T]]) -> None:
    """Add all elements from ``other`` in ``into``, updating the sets to their
    union."""
    for k, v in other.items():
        if k in into:
            into[k].update(v)
        else:
            into[k] = v


def _merge_components(components: List[Dict[T, Set[T]]], indices: List[int]) -> None:
    assert len(indices) > 1, "Merging requires at least two components"
    indices.sort()
    for i in indices[1:]:
        _merge_dicts_of_sets(into=components[indices[0]], other=components[i])
    for i in reversed(indices[1:]):
        del components[i]


def _find_connected_vertices(component_dict: Dict[T, Set[T]], start: T) -> Set[T]:
    explored: Set[T] = set()
    explore_queue: List[T] = [start]
    while explore_queue:
        node = explore_queue.pop()  # DFS
        explored.add(node)
        explore_queue.extend(c for c in component_dict[node] if c not in explored)
    return explored


def _update_components_map(
    components: List[Dict[T, Set[T]]], changes: _Changes[T]
) -> None:
    # pylint: disable=too-many-locals
    for vertex_added in changes.vertices_added:
        components.append({vertex_added: set()})
    for edge_added in changes.edges_added:
        component_with_a = _find_index_of_component_with_vertex(
            components=components, vertex=edge_added.a
        )
        component_with_b = _find_index_of_component_with_vertex(
            components=components, vertex=edge_added.b
        )
        components[component_with_a][edge_added.a].add(edge_added.b)
        components[component_with_b][edge_added.b].add(edge_added.a)
        if component_with_a != component_with_b:
            _merge_components(
                components=components,
                indices=[component_with_a, component_with_b],
            )
    components_with_edge_removed: List[int] = []
    for edge_removed in changes.edges_removed:
        component = _find_index_of_component_with_vertex(
            components=components, vertex=edge_removed.a
        )
        components_with_edge_removed.append(component)
        components[component][edge_removed.a].remove(edge_removed.b)
        components[component][edge_removed.b].remove(edge_removed.a)
    for vertex_removed in changes.vertices_removed:
        component = _find_index_of_component_with_vertex(
            components=components, vertex=vertex_removed
        )
        # Remove mappings from removed edge
        del components[component][vertex_removed]
        for target in components[component].values():
            # Remove mappings to removed edge (if it was not already removed
            # by an edge removal)
            if vertex_removed in target:
                target.remove(vertex_removed)
    component_splits: Dict[int, List[Dict[T, Set[T]]]] = {}
    for component in components_with_edge_removed:
        orig_vertices = set(iter(components[component]))
        component_splits[component] = []
        while orig_vertices:
            connected_vertices = _find_connected_vertices(
                component_dict=components[component],
                start=next(iter(orig_vertices)),
            )
            component_splits[component].append(
                {
                    v: incident_set
                    for v, incident_set in components[component].items()
                    if v in connected_vertices
                }
            )
            orig_vertices.difference_update(connected_vertices)
        if len(component_splits[component]) < 2:
            # There is no split of that component
            del component_splits[component]
    for original_index, new_components in component_splits.items():
        components[original_index] = new_components[0]
        components.extend(new_components[1:])


class LogLWWGraph(LWWGraph[T]):
    """Simplistic LWW-element-graph local process that records operations as
    they come to an in-memory log. There is no garbage collection, no log
    compression, no persistence to disk, etc."""

    def __init__(self, clock: Clock) -> None:
        self.clock = clock
        self._oplog: List[LWWGraphOperation] = []

    def __contains__(self, item: Union[T, Edge[T]]) -> bool:
        if isinstance(item, Edge):
            return item in self._current_state[1]
        return item in self._current_state[0]

    @property
    def _current_state(self) -> Tuple[Set[T], Set[BaseEdge[T]], List[Dict[T, Set[T]]]]:
        """Iterate over the operations log to determine which vertices and
        edges are currently present."""
        # Mapping: operation (add/del edge/vertex) -> edge/vertex -> last timestamp
        last_op: DefaultDict[
            LWWGraphOpName, Dict[Union[T, BaseEdge[T]], int]
        ] = defaultdict(dict)
        # Known vertices and edges at current processing point
        vertices: Set[T] = set()
        edges: Set[BaseEdge[T]] = set()
        components: List[Dict[T, Set[T]]] = []
        # Go through the sorted log
        for op in sorted(self._oplog, key=lambda o: (o.ts, OP_ORDER[o.op])):
            last_op[op.op][op.arg] = op.ts
            changes: Optional[_Changes[T]] = None  # used for components update
            if op.op == "add_e":
                changes = _process_add_edge_operation(
                    op=op, last_operations=last_op, edges=edges
                )
            elif op.op == "del_e":
                changes = _process_delete_edge_operation(op=op, edges=edges)
            elif op.op == "add_v":
                changes = _process_add_vertex_operation(
                    op=op, last_operations=last_op, vertices=vertices
                )
            elif op.op == "del_v":
                changes = _process_delete_vertex_operation(
                    op=op, last_operations=last_op, vertices=vertices, edges=edges
                )
            else:
                assert_never(op.op)
            # Update the components map
            if changes:
                _update_components_map(components=components, changes=changes)
        return vertices, edges, components

    @property
    def vertices(self) -> Iterable[T]:
        """Return the set of vertices that defines this graph"""
        return self._current_state[0]

    @property
    def edges(self) -> Iterable[BaseEdge[T]]:
        """Return the set of edges that defines this graph, without the edges
        with an invalid vertex."""
        return self._current_state[1]

    @property
    def components(self) -> Iterable[Mapping[T, Set[T]]]:
        """Return an iterable of all graph components. Each component is
        represented by a mapping from each vertex to its incident edges."""
        return self._current_state[2]

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
