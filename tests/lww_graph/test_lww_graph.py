from typing import Any, List

import pytest

from crdt.lww_graph.edge import FrozenEdge
from crdt.lww_graph.impl.log_lww_graph import LogLWWGraph
from crdt.lww_graph.interface import LWWGraph


def make_new_instance_of_each_impl() -> List[LWWGraph]:
    return [
        LogLWWGraph(),
    ]


def edge(a: Any, b: Any) -> FrozenEdge:
    return FrozenEdge(a, b)


@pytest.mark.parametrize("graph", make_new_instance_of_each_impl())
def test_correctness_via_interface(
    graph: LWWGraph[int],
) -> None:
    assert len(set(graph.edges.elements)) == 0, "New graph should be empty"
    assert len(set(graph.vertices.elements)) == 0, "New graph should be empty"
    graph.add_vertex(item=1)
    graph.add_vertex(item=2)
    graph.add_edge(item=edge(1, 2))
    graph.remove_vertex(item=1)
    graph.add_vertex(item=1)
    graph.add_edge(item=edge(1, 2))
    graph.remove_edge(item=edge(1, 2))
