from typing import Tuple

from .axis_state import AxisState
from .shot_classification import ShotClassification
from .shot_filter import ShotFilter
from ..base import MovementClassifierInterface


class MovementClassifier(MovementClassifierInterface):
    """
    ppClassifier MovementClassifier.

    Tracks horizontal and vertical movement axes plus left Shift and left Ctrl.
    Fires "Not detected" when no movement key was pressed within 500 ms of the shot.

    Key strings for special keys:
        Shift  → "SHIFT"
        Ctrl   → "CTRL"
    """

    NO_MOVEMENT_WINDOW_MS = 500.0

    def __init__(
        self,
        *,
        vertical_keys: Tuple[str, str] = ("W", "S"),
        horizontal_keys: Tuple[str, str] = ("A", "D"),
    ) -> None:
        v_keys = tuple(key.upper() for key in vertical_keys)
        h_keys = tuple(key.upper() for key in horizontal_keys)
        if len(set(v_keys)) != 2:
            raise ValueError(
                f"vertical_keys must contain two distinct keys, got {vertical_keys}"
            )
        if len(set(h_keys)) != 2:
            raise ValueError(
                f"horizontal_keys must contain two distinct keys, got {horizontal_keys}"
            )
        self.vertical = AxisState(keys=v_keys)
        self.horizontal = AxisState(keys=h_keys)
        self._shot_filter = ShotFilter()
        self._shift_held: bool = False
        self._ctrl_held: bool = False
        self._last_movement_time: float = None  # type: ignore[assignment]

        self._all_movement_keys = set(v_keys) | set(h_keys)

    def on_press(self, key: str, timestamp: float) -> None:
        upper = key.upper()

        if upper == "SHIFT":
            self._shift_held = True
            return
        if upper == "CTRL":
            self._ctrl_held = True
            return

        if upper in self.vertical.keys:
            self.vertical.on_press(upper, timestamp)
            self._last_movement_time = timestamp
        elif upper in self.horizontal.keys:
            self.horizontal.on_press(upper, timestamp)
            self._last_movement_time = timestamp

    def on_release(self, key: str, timestamp: float) -> None:
        upper = key.upper()

        if upper == "SHIFT":
            self._shift_held = False
            return
        if upper == "CTRL":
            self._ctrl_held = False
            return

        if upper in self.vertical.keys:
            self.vertical.on_release(upper, timestamp)
        elif upper in self.horizontal.keys:
            self.horizontal.on_release(upper, timestamp)

    def classify_shot(self, shot_time: float) -> ShotClassification:
        # "Not detected": no movement at all, or last movement was > 500 ms ago
        if (
            self._last_movement_time is None
            or (shot_time - self._last_movement_time) >= self.NO_MOVEMENT_WINDOW_MS
        ):
            # Still need to reset axis state so it doesn't bleed into next shot
            self.vertical.classify_shot(shot_time)
            self.horizontal.classify_shot(shot_time)
            return ShotClassification(label="Not detected")

        h_result = self.horizontal.classify_shot(shot_time)
        v_result = self.vertical.classify_shot(shot_time)

        raw = ShotClassification.from_axis_results(
            h_result,
            v_result,
            shift_held=self._shift_held,
            ctrl_held=self._ctrl_held,
        )

        if raw.label == "Bad" and h_result[0] == "Bad" and v_result[0] == "Bad":
            raw.sub_label = "No counter-strafe"

        return self._shot_filter.apply(raw)
