"""Utilities to help type-checking"""
from typing import NoReturn


def assert_never(value: NoReturn) -> NoReturn:
    """Use as the last "else" clause of an exhaustive switch over Enum or
    Literal values to help verify exhaustiveness.

    Source: https://hakibenita.com/python-mypy-exhaustive-checking"""
    assert False, f"Unhandled value of type {type(value).__name__}: {value}"
