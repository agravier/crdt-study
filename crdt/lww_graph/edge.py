"""Edges are serializable, unordered pairs of atoms. This module implements
them as Pydantic BaseModel and also using frozenset."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods, invalid-name
from __future__ import annotations

from abc import abstractmethod
from typing import Any, Final, Generic, Tuple, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T", covariant=True)

# We roll out our own hash function for edges. This constant determines how
# large that space is in bits
_HASH_BITS: Final[int] = 64


class Edge(Generic[T]):
    """This abstract class defines equality and a hash function on undirected
    edges"""

    @property
    @abstractmethod
    def vertices(self) -> Tuple[T, T]:
        ...

    def __contains__(self, item: Any) -> bool:
        """Check whether the argument is one of the vertices that form this
        edge."""
        return item in self.vertices

    def __hash__(self) -> int:
        a, b = self.vertices
        ha, hb = hash(a), hash(b)
        if hb > ha:
            ha, hb = hb, ha
        return (ha << (_HASH_BITS // 2) ^ hb) & (2 ** _HASH_BITS - 1)

    def __eq__(self, other: Any) -> bool:
        if isinstance(other, Edge):
            a1, b1 = self.vertices
            a2, b2 = other.vertices
            return (a1 == a2 and b1 == b2) or (a1 == b2 and b1 == a2)
        return False


class BaseEdge(GenericModel, Edge[T]):
    """Serializable edge implementation based on BaseModel"""

    a: T
    b: T

    @property
    def vertices(self) -> Tuple[T, T]:
        return self.a, self.b

    def __contains__(self, item: Any) -> bool:
        """Check whether the argument is one of the vertices that form this
        edge."""
        # pylint: disable=consider-using-in
        return item == self.a or item == self.b

    @classmethod
    def from_edge(cls, edge: Edge[T]) -> BaseEdge[T]:
        if isinstance(edge, BaseEdge):
            return edge
        a, b = edge.vertices
        return BaseEdge(a=a, b=b)

    class Config:
        frozen = True


class FrozenEdge(Edge[T]):
    """Edge implementation based on the built-in frozenset"""

    def __init__(self, a: T, b: T) -> None:
        self._vertices: Final[frozenset] = frozenset([a, b])

    @property
    def vertices(self) -> Tuple[T, T]:
        try:
            first_elem, second_elem = self._vertices
        except ValueError:
            (first_elem,) = (second_elem,) = self._vertices
        return first_elem, second_elem

    def __contains__(self, item: Any) -> bool:
        """Check whether the argument is one of the vertices that form this
        edge."""
        return item in self._vertices

    @classmethod
    def from_edge(cls, edge: Edge[T]) -> FrozenEdge[T]:
        return FrozenEdge(*edge.vertices)
