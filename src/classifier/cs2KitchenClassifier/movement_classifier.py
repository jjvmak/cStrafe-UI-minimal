from typing import Optional, Tuple
from .axis_state import AxisState
from .shot_classification import ShotClassification
from ..base import DebugLogger, MovementClassifierInterface


def _fmt_axis(label: str, val1: Optional[float], val2) -> str:
    """Format a single axis result tuple as a human-readable string."""
    if label == "Counter-strafe" and val1 is not None and val2 is not None:
        return f"Counter-strafe | CS: {val1:.0f} ms | Delay: {val2:.0f} ms"
    if label == "Overlap" and val1 is not None:
        return f"Overlap | {val1:.0f} ms"
    if label == "Bad" and val2 is not None:
        return f"Bad ({val2})"
    return label


class MovementClassifier(MovementClassifierInterface):
    """
    Classifies player movement based on key presses and releases.

    By default the classifier tracks the conventional vertical (forward/backward)
    and horizontal (left/right) movement keys. Custom key bindings can be
    supplied to accommodate different keyboard layouts or player preferences.
    """

    def __init__(
        self,
        *,
        vertical_keys: Tuple[str, str] = ("W", "S"),
        horizontal_keys: Tuple[str, str] = ("A", "D"),
        debug_logger: Optional[DebugLogger] = None,
    ) -> None:
        v_keys = tuple(key.upper() for key in vertical_keys)
        h_keys = tuple(key.upper() for key in horizontal_keys)
        if len(set(v_keys)) != 2:
            raise ValueError(f"vertical_keys must contain two distinct keys, got {vertical_keys}")
        if len(set(h_keys)) != 2:
            raise ValueError(f"horizontal_keys must contain two distinct keys, got {horizontal_keys}")
        self.vertical = AxisState(keys=v_keys)
        self.horizontal = AxisState(keys=h_keys)
        self._debug = debug_logger

    def on_press(self, key: str, timestamp: float) -> None:
        if key in self.vertical.keys:
            if self._debug:
                self._debug.log(f"[KEY] \u2193 {key} @ {timestamp:.0f} ms")
            self.vertical.on_press(key, timestamp)
        elif key in self.horizontal.keys:
            if self._debug:
                self._debug.log(f"[KEY] \u2193 {key} @ {timestamp:.0f} ms")
            self.horizontal.on_press(key, timestamp)

    def on_release(self, key: str, timestamp: float) -> None:
        if key in self.vertical.keys:
            if self._debug:
                self._debug.log(f"[KEY] \u2191 {key} @ {timestamp:.0f} ms")
            self.vertical.on_release(key, timestamp)
        elif key in self.horizontal.keys:
            if self._debug:
                self._debug.log(f"[KEY] \u2191 {key} @ {timestamp:.0f} ms")
            self.horizontal.on_release(key, timestamp)

    def classify_shot(self, shot_time: float) -> ShotClassification:
        v_label, v_val1, v_val2 = self.vertical.classify_shot(shot_time)
        h_label, h_val1, h_val2 = self.horizontal.classify_shot(shot_time)

        if self._debug:
            self._debug.log(f"[AXIS:V] {_fmt_axis(v_label, v_val1, v_val2)}")
            self._debug.log(f"[AXIS:H] {_fmt_axis(h_label, h_val1, h_val2)}")

        negativity = {
            "Overlap": 2,
            "Counter-strafe": 1,
            "Bad": 0,
        }
        v_score = negativity.get(v_label, 0)
        h_score = negativity.get(h_label, 0)
        if v_score > h_score:
            label, val1, val2 = v_label, v_val1, v_val2
        elif h_score > v_score:
            label, val1, val2 = h_label, h_val1, h_val2
        else:
            if v_val1 is not None and h_val1 is not None:
                if v_val1 >= h_val1:
                    label, val1, val2 = v_label, v_val1, v_val2
                else:
                    label, val1, val2 = h_label, h_val1, h_val2
            elif v_val1 is not None:
                label, val1, val2 = v_label, v_val1, v_val2
            else:
                label, val1, val2 = h_label, h_val1, h_val2

        if self._debug:
            self._debug.log(f"[SHOT] \u2192 {_fmt_axis(label, val1, val2)}")

        if label == "Counter-strafe":
            return ShotClassification(label=label, cs_time=val1, shot_delay=val2)
        elif label == "Overlap":
            return ShotClassification(label=label, overlap_time=val1)
        return ShotClassification(label=label)
