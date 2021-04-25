"""Interface classes for the monotonic clock implementations."""
# pylint: disable=missing-class-docstring,missing-function-docstring,
# pylint: disable=too-few-public-methods
from abc import abstractmethod
from typing import Protocol


class ClockError(Exception):
    """Raised when clock monotonicity is violated, or when the underlying
    implementation fails"""


class Clock(Protocol):
    @property
    @abstractmethod
    def nanoseconds(self) -> int:
        pass
