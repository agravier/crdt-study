"""Black-box unit tests of LWWGraph implementations"""
from typing import Any, List

import pytest

from crdt.clock.impl.mocktime import MockMonotonicClock
from crdt.lww_graph.edge import FrozenEdge
from crdt.lww_graph.impl.log_lww_graph import LogLWWGraph
from crdt.lww_graph.interface import LWWGraph


def make_new_instance_of_each_impl() -> List[LWWGraph]:
    """Make a new empty instance of each implementation of the LWWGraph interface,
    backed by a mock clock."""
    return [
        LogLWWGraph(clock=MockMonotonicClock(0)),
    ]


def edge(a: Any, b: Any) -> FrozenEdge:
    """Convenience function to create an edge between two atoms"""
    return FrozenEdge(a, b)


@pytest.mark.parametrize("graph", make_new_instance_of_each_impl())
def test_correctness_via_interface(
    graph: LWWGraph[int],
) -> None:
    """Run simple correctness tests on each implementation of LWWGraph."""
    assert len(set(graph.edges)) == 0, "New graph should be empty"
    assert len(set(graph.vertices)) == 0, "New graph should be empty"
    # Add vertices
    graph.add_vertex(vertex=1)
    graph.add_vertex(vertex=2)
    assert set(graph.vertices) == {1, 2}
    # Add edge
    assert set(graph.edges) == set()
    graph.add_edge(edge=edge(1, 2))
    assert set(graph.edges) == {edge(1, 2)}
    # Remove vertex also removes attached edges
    graph.remove_vertex(vertex=1)
    assert set(graph.vertices) == {2}
    assert set(graph.edges) == set()
    # Add edge with a non-existent vertex
    graph.add_edge(edge=edge(1, 2))
    assert set(graph.edges) == set()
    # Add vertex is idempotent
    graph.add_vertex(vertex=1)
    graph.add_vertex(vertex=1)
    assert set(graph.vertices) == {1, 2}
    # Idempotence of add edge
    graph.add_edge(edge=edge(1, 2))
    graph.add_edge(edge=edge(1, 2))
    assert set(graph.edges) == {edge(1, 2)}
    # Add edge twice still only requires one remove_edge
    graph.remove_edge(edge=edge(1, 2))
    assert set(graph.edges) == set()
    assert set(graph.vertices) == {1, 2}
    # Remove edge is idempotent
    graph.add_edge(edge=edge(1, 2))
    assert set(graph.edges) == {edge(1, 2)}
    graph.remove_edge(edge=edge(1, 2))
    assert set(graph.edges) == set()
    graph.remove_edge(edge=edge(1, 2))
    assert set(graph.edges) == set()
    # Remove vertex is idempotent
    assert set(graph.vertices) == {1, 2}
    graph.remove_vertex(vertex=1)
    assert set(graph.vertices) == {2}
    graph.remove_vertex(vertex=1)
    assert set(graph.vertices) == {2}
    graph.remove_vertex(vertex=2)
    assert set(graph.vertices) == set()
    graph.remove_vertex(vertex=2)
    assert set(graph.vertices) == set()
