"""This class offers an interface and an implementation for the operations that
are serialized as part of """
# pylint: disable=too-few-public-methods
from typing import Any, Dict, Generic, Literal, TypeVar, Union

from pydantic import validator
from pydantic.generics import GenericModel

from crdt.lww_graph.edge import BaseEdge

T = TypeVar("T")

LWWSetOpName = Literal["add", "del"]


class LWWSetOperation(GenericModel, Generic[T]):
    """Serialized representation of an operation on a LWWSet"""

    op: LWWSetOpName  # Operation name
    arg: T  # Operation argument
    ts: int  # Timestamp


# We use the suffixes "_e" and "_v" to differentiate vertex and edge ops.
LWWGraphOpName = Literal["add_e", "add_v", "del_e", "del_v"]


class LWWGraphOperation(GenericModel, Generic[T]):
    """Serialized representation of an operation on a LWWGraph"""

    # pylint: disable=no-self-argument,no-self-use

    op: LWWGraphOpName
    arg: Union[T, BaseEdge[T]]
    ts: int

    @validator("args")
    def args_type(
        cls, v: Union[T, BaseEdge[T]], values: Dict[str, Any], **_: Any
    ) -> Union[T, BaseEdge[T]]:
        """Verify that operations on edges receive a BaseEdge as argument."""
        if "op" in values:
            if values["op"].endswith("_e") and not isinstance(v, BaseEdge):
                raise TypeError(
                    f"The operation {values['op']} can't take argument {v} of "
                    f"type {type(v)}. A BaseEdge is expected."
                )
            # Note that we don't want to test the vertex operations arg type
        return v
