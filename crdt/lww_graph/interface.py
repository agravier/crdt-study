"""Interface classes for the LWW-Element-Graph implementations. They are
specified as protocols, so they don't need to be explicitly declared as
parents."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods

from __future__ import annotations

from abc import abstractmethod
from typing import (
    Dict,
    Iterable,
    List,
    Mapping,
    Optional,
    Protocol,
    Set,
    TypeVar,
    Union,
)

from crdt.lww_graph.edge import Edge, FrozenEdge
from crdt.lww_graph.operation import LWWGraphOperation

T = TypeVar("T")


class LWWGraphError(Exception):
    pass


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


def _backtrack(backtracking_map: Dict[T, T], end: T, start: T) -> List[Edge[T]]:
    reverse_path = []
    prev = end
    while end != start:
        end = backtracking_map[end]
        reverse_path.append(FrozenEdge(end, prev))
        prev = end
    return list(reversed(reverse_path))


def find_shortest_path(graph: LWWGraph[T], a: T, b: T) -> Optional[List[Edge[T]]]:
    try:
        component = next(c for c in graph.components if a in c)
    except StopIteration:
        return None
    if b not in component:
        return None
    backtrack_link: Dict[T, T] = {}
    explored: Set[T] = set()
    explore_queue: List[T] = [a]
    while explore_queue:
        node = explore_queue.pop(0)  # BFS
        if node == b:
            return _backtrack(backtracking_map=backtrack_link, end=b, start=a)
        explored.add(node)
        children = [c for c in component[node] if c not in explored]
        backtrack_link.update({c: node for c in children})
        explore_queue.extend(children)
    raise LWWGraphError(f"Malformed graph component map: {graph.components}")
