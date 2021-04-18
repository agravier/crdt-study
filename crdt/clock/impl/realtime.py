"""The realtime module defines a real-time monotonic clock."""
import time

# pylint: disable=too-few-public-methods


class MonotonicRealTimeClock:
    """This clock uses python's monotonic clock to track the time since a
    reference time set during creation"""

    def __init__(self, reference_time_now_ns: int) -> None:
        """Initialize this clock with a reference time. Due to the
        unpredictable execution duration, a negative skew is to be expected.

        :param reference_time_now_ns: reference time at the moment of creation
        """
        self.zero = time.monotonic_ns()
        self.zero -= reference_time_now_ns

    @property
    def nanoseconds(self) -> int:
        """The wall clock time elapsed in the reference timeframe in
        nanoseconds"""
        return time.monotonic_ns() - self.zero
