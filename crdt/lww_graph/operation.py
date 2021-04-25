"""This class offers an interface and an implementation for the operations that
are serialized as part of the conflict-free, distributed usage of LWWGraph."""
# pylint: disable=too-few-public-methods
from typing import Any, Dict, Generic, Literal, TypeVar, Union

from pydantic import validator
from pydantic.generics import GenericModel

from crdt.lww_graph.edge import BaseEdge, Edge

T = TypeVar("T")


# We use the suffixes "_e" and "_v" to differentiate vertex and edge ops.
LWWGraphOpName = Literal["add_e", "add_v", "del_e", "del_v"]


class LWWGraphOperation(GenericModel, Generic[T]):
    """Serialized representation of an operation on a LWWGraph"""

    # pylint: disable=no-self-argument,no-self-use

    op: LWWGraphOpName
    arg: Union[T, BaseEdge[T]]
    ts: int

    @validator("arg")
    def arg_type(
        cls, v: Union[T, BaseEdge[T]], values: Dict[str, Any]
    ) -> Union[T, BaseEdge[T]]:
        """Verify that operations on edges receive a BaseEdge as argument."""
        if "op" in values:
            if values["op"].endswith("_e"):
                if not isinstance(v, Edge):
                    raise TypeError(
                        f"The operation {values['op']} can't take argument {v} "
                        f"of type {type(v)}. A BaseEdge is expected."
                    )
                v = BaseEdge.from_edge(v)
            # Note that we don't want to test the vertex operations arg type
        return v
