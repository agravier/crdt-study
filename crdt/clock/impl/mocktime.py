"""The mocktime module defines a programmable clock used for testing."""
from typing import Optional

# pylint: disable=missing-function-docstring


class MockMonotonicClock:
    """This clock returns the next scheduled time if set, or the previous
    incremented by step_size (default 1) otherwise"""

    def __init__(self, reference_time_now_ns: int) -> None:
        """Initialize this clock with a reference time.

        Params
            reference_time_now_ns: reference time at the moment of creation
        """
        self.now = reference_time_now_ns
        self._step_size = 1
        self._next_tick: Optional[int] = None

    @property
    def step_size(self) -> int:
        return self._step_size

    @step_size.setter
    def step_size(self, step_size: int) -> None:
        assert step_size >= 0, "The step size can't be negative"
        self._step_size = step_size

    @property
    def next_tick(self) -> int:
        if self._next_tick is not None:
            return self._next_tick
        return self.now + self.step_size

    @next_tick.setter
    def next_tick(self, nanoseconds: int) -> None:
        assert nanoseconds >= self.now, "The clock must be monotonic"
        self._next_tick = nanoseconds

    @property
    def nanoseconds(self) -> int:
        self.now = self.next_tick
        return self.now
