"""This class offers an interface and an implementation for the operations that
are serialized as part of the conflict-free, distributed usage of LWWSet."""
# pylint: disable=too-few-public-methods
from typing import Generic, Literal, TypeVar

from pydantic.generics import GenericModel

T = TypeVar("T")

LWWSetOpName = Literal["add", "del"]


class LWWSetOperation(GenericModel, Generic[T]):
    """Serialized representation of an operation on a LWWSet"""

    op: LWWSetOpName  # Operation name
    arg: T  # Operation argument
    ts: int  # Timestamp
