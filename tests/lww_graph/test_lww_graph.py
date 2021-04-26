"""Black-box unit tests of LWWGraph implementations. Functionalities:
- add a vertex/edge,
- remove a vertex/edge,
- check if a vertex is in the graph,
- query for all vertices connected to a vertex,
- find any path between two vertices,
- merge with concurrent changes from other graph/replica."""
from typing import Any, Iterable, List
from unittest import TestCase

import pytest

from crdt.clock.impl.mocktime import MockMonotonicClock
from crdt.lww_graph.edge import FrozenEdge
from crdt.lww_graph.impl.log_lww_graph import LogLWWGraph
from crdt.lww_graph.interface import LWWGraph, find_shortest_path


def make_new_instance_of_each_impl() -> List[LWWGraph]:
    """Make a new empty instance of each implementation of the LWWGraph
    interface, backed by a mock clock."""
    return [
        LogLWWGraph(clock=MockMonotonicClock(0)),
    ]


def edge(a: Any, b: Any) -> FrozenEdge:
    """Convenience function to create an edge between two atoms"""
    return FrozenEdge(a, b)


def assert_same_counts(first: Iterable, second: Iterable, message: str = None) -> None:
    """Convenience wrapper around TestCase.assertCountEqual"""
    return TestCase().assertCountEqual(first, second, msg=message)


@pytest.mark.parametrize("graph", make_new_instance_of_each_impl())
def test_correctness_via_interface__ordered(
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
    # Adding back the removed vertex should NOT restore the previously
    # cascaded edge deletions.
    graph.add_vertex(vertex=1)
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


@pytest.mark.parametrize("graph", make_new_instance_of_each_impl())
def test_correctness_via_interface__unordered(
    graph: LWWGraph[int],
) -> None:
    """Run simple correctness tests on each implementation of LWWGraph."""
    assert len(set(graph.edges)) == 0, "New graph should be empty"
    assert len(set(graph.vertices)) == 0, "New graph should be empty"
    # Add vertices
    graph.add_vertex(vertex=1, ts=100)
    graph.add_vertex(vertex=2, ts=100)
    assert set(graph.vertices) == {1, 2}
    # Add edge BEFORE the vertices existed
    assert set(graph.edges) == set()
    graph.add_edge(edge=edge(1, 2), ts=10)
    assert set(graph.edges) == set()
    # Remove vertex also removes attached edges, even with the wrong call order
    # but correct logical order (accounting for deletion precedence)
    assert set(graph.vertices) == {1, 2}
    graph.remove_vertex(vertex=1, ts=200)
    graph.add_edge(edge=edge(1, 2), ts=200)
    assert set(graph.edges) == set()
    assert set(graph.vertices) == {2}
    # Add back vertex doesn't restore the deleted edge
    graph.add_vertex(vertex=1, ts=201)
    assert set(graph.vertices) == {1, 2}
    assert set(graph.edges) == set()
    graph.add_edge(edge=edge(1, 2), ts=201)
    assert set(graph.edges) == {edge(1, 2)}


@pytest.mark.parametrize("graph", make_new_instance_of_each_impl())
def test_components_via_interface__unordered(
    graph: LWWGraph[str],
) -> None:
    """Run simple tests of the correctness of the graph components for each
    implementation of LWWGraph."""
    assert_same_counts(graph.components, [])
    graph.add_edge(edge("arm 1", "centre"), ts=1000)
    assert_same_counts(graph.components, [])
    graph.add_vertex("arm 1", ts=100)
    assert_same_counts(graph.components, [{"arm 1": set()}])
    graph.add_edge(edge("arm 3", "centre"), ts=1003)
    assert_same_counts(graph.components, [{"arm 1": set()}])
    graph.add_edge(edge("arm 5", "centre"), ts=1005)
    assert_same_counts(graph.components, [{"arm 1": set()}])
    graph.add_vertex("arm 2", ts=100)
    assert_same_counts(graph.components, [{"arm 1": set()}, {"arm 2": set()}])
    graph.add_vertex("centre", ts=1000)
    assert_same_counts(
        graph.components, [{"arm 1": {"centre"}, "centre": {"arm 1"}}, {"arm 2": set()}]
    )
    graph.add_vertex("arm 3", ts=100)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": {"centre"},
                "arm 3": {"centre"},
                "centre": {"arm 1", "arm 3"},
            },
            {"arm 2": set()},
        ],
    )
    graph.add_edge(edge("arm 2", "centre"), ts=1002)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": {"centre"},
                "arm 2": {"centre"},
                "arm 3": {"centre"},
                "centre": {"arm 1", "arm 2", "arm 3"},
            },
        ],
    )
    graph.add_vertex("arm 4", ts=100)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": {"centre"},
                "arm 2": {"centre"},
                "arm 3": {"centre"},
                "centre": {"arm 1", "arm 2", "arm 3"},
            },
            {"arm 4": set()},
        ],
    )
    graph.add_vertex("arm 5", ts=900)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": {"centre"},
                "arm 2": {"centre"},
                "arm 3": {"centre"},
                "arm 5": {"centre"},
                "centre": {"arm 1", "arm 2", "arm 3", "arm 5"},
            },
            {"arm 4": set()},
        ],
    )
    graph.add_edge(edge("arm 4", "centre"), ts=1004)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": {"centre"},
                "arm 2": {"centre"},
                "arm 3": {"centre"},
                "arm 4": {"centre"},
                "arm 5": {"centre"},
                "centre": {"arm 1", "arm 2", "arm 3", "arm 5", "arm 4"},
            },
        ],
    )
    graph.remove_vertex("centre", ts=1000)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": set(),
            },
            {
                "arm 2": set(),
            },
            {
                "arm 3": set(),
            },
            {
                "arm 4": set(),
            },
            {
                "arm 5": set(),
            },
        ],
    )
    graph.add_edge(edge("arm 4", "arm 4"), ts=1010)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": set(),
            },
            {
                "arm 2": set(),
            },
            {
                "arm 3": set(),
            },
            {
                "arm 4": {"arm 4"},
            },
            {
                "arm 5": set(),
            },
        ],
    )
    graph.add_vertex("centre", ts=1001)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": set(),
            },
            {
                "arm 2": {"centre"},
                "arm 3": {"centre"},
                "arm 4": {"centre", "arm 4"},
                "arm 5": {"centre"},
                "centre": {"arm 2", "arm 3", "arm 5", "arm 4"},
            },
        ],
    )
    graph.remove_vertex("arm 4", ts=1010)
    assert_same_counts(
        graph.components,
        [
            {
                "arm 1": set(),
            },
            {
                "arm 2": {"centre"},
                "arm 3": {"centre"},
                "arm 5": {"centre"},
                "centre": {"arm 2", "arm 3", "arm 5"},
            },
        ],
    )


@pytest.mark.parametrize("graph", make_new_instance_of_each_impl())
def test_find_shortest_path(
    graph: LWWGraph[int],
) -> None:
    """Test the function to find the shortest path between two vertices."""
    graph.add_vertex(1)
    graph.add_vertex(2)
    graph.add_vertex(3)
    graph.add_vertex(4)
    graph.add_vertex(5)
    graph.add_edge(edge(1, 2))
    graph.add_edge(edge(2, 3))
    graph.add_edge(edge(3, 4))
    graph.add_edge(edge(3, 5))
    assert find_shortest_path(graph=graph, a=1, b=5) == [
        edge(1, 2),
        edge(2, 3),
        edge(3, 5),
    ]
    graph.add_vertex(10)
    graph.add_vertex(20)
    graph.add_vertex(30)
    graph.add_vertex(40)
    graph.add_vertex(50)
    graph.add_vertex(60)
    graph.add_edge(edge(10, 20))
    graph.add_edge(edge(20, 30))
    graph.add_edge(edge(30, 40))
    graph.add_edge(edge(40, 50))
    graph.add_edge(edge(50, 60))
    assert find_shortest_path(graph=graph, a=20, b=60) == [
        edge(20, 30),
        edge(30, 40),
        edge(40, 50),
        edge(50, 60),
    ]
    assert find_shortest_path(graph=graph, a=2, b=50) is None
    assert find_shortest_path(graph=graph, a=1, b=1) == []
    assert find_shortest_path(graph=graph, a=1000, b=50) is None
    assert find_shortest_path(graph=graph, a=1, b=5000) is None
