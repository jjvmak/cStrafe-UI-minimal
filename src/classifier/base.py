from abc import ABC, abstractmethod
from typing import Any, Callable, Optional


class DebugLogger:
    """
    Simple debug logger for classifiers.

    Accepts a callback (e.g. ``overlay.log_debug``) and provides a ``log()``
    method.  Classifiers that accept a ``debug_logger`` kwarg call
    ``self._debug.log(msg)`` to emit human-readable debug events.

    Usage::

        logger = DebugLogger(overlay.log_debug)
        classifier = MovementClassifier(..., debug_logger=logger)
    """

    def __init__(self, callback: Callable[[str], None]) -> None:
        self._callback = callback

    def log(self, message: str) -> None:
        self._callback(message)


class MovementClassifierInterface(ABC):
    @abstractmethod
    def on_press(self, key: str, timestamp: float) -> None:
        """Handle a key press for the given key at the given timestamp."""

    @abstractmethod
    def on_release(self, key: str, timestamp: float) -> None:
        """Handle a key release for the given key at the given timestamp."""

    @abstractmethod
    def classify_shot(self, shot_time: float) -> Any:
        """Return a shot classification object for a shot at shot_time."""


class ShotClassificationInterface(ABC):
    @abstractmethod
    def to_display_string(self) -> str:
        """Return a human-friendly multi-line description of the classification."""


class ShotFilterInterface(ABC):
    @abstractmethod
    def apply(self, raw: "ShotClassificationInterface") -> "ShotClassificationInterface":
        """Apply threshold rules to a raw classification and return the final one."""


class AxisStateInterface(ABC):
    @abstractmethod
    def on_press(self, key: str, timestamp: float) -> None:
        """Handle a key press for the given key at the given timestamp."""

    @abstractmethod
    def on_release(self, key: str, timestamp: float) -> None:
        """Handle a key release for the given key at the given timestamp."""

    @abstractmethod
    def classify_shot(self, shot_time: float):
        """Return a tuple describing the classification for a shot at shot_time."""
