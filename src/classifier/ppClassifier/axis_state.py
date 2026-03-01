from typing import Optional, Tuple, Set, Dict

from ..base import AxisStateInterface


class AxisState(AxisStateInterface):
    """
    Tracks the state of a single movement axis (e.g. A/D or W/S).

    Identical detection logic to cs2KitchenClassifier's AxisState.
    All timestamps are in milliseconds.
    Always returns a 3-tuple from classify_shot.
    """

    MICRO_CANDIDATE_THRESHOLD_MS = 80.0

    def __init__(self, keys: Tuple[str, str]) -> None:
        self.keys: Tuple[str, str] = keys
        self.held_keys: Set[str] = set()
        self.press_times: Dict[str, float] = {}
        self.cs_release_key: Optional[str] = None
        self.cs_release_time: Optional[float] = None
        self.cs_press_key: Optional[str] = None
        self.cs_press_time: Optional[float] = None
        self.overlap_start_time: Optional[float] = None
        self.micro_candidate_duration: Optional[float] = None

    def on_press(self, key: str, timestamp: float) -> None:
        if key not in self.keys:
            return
        other = self.keys[0] if key == self.keys[1] else self.keys[1]
        self.held_keys.add(key)
        self.press_times[key] = timestamp
        if other in self.held_keys and self.overlap_start_time is None:
            self.overlap_start_time = timestamp
        if self.cs_release_key == other and self.cs_press_time is None:
            self.cs_press_key = key
            self.cs_press_time = timestamp
        self.micro_candidate_duration = None

    def on_release(self, key: str, timestamp: float) -> None:
        if key not in self.keys:
            return
        press_time = self.press_times.get(key)
        if press_time is not None:
            duration = timestamp - press_time
            if duration < self.MICRO_CANDIDATE_THRESHOLD_MS:
                self.micro_candidate_duration = duration
            else:
                self.micro_candidate_duration = None
        self.held_keys.discard(key)
        if not self.held_keys:
            self.overlap_start_time = None
        # Only start a new CS tracking cycle when releasing a key that is NOT
        # the counter-press key.  If the player releases the CS key itself
        # (the brief D/A tap to stop momentum) we must preserve cs_press_key/time
        # so that classify_shot can still detect the counter-strafe.
        if key != self.cs_press_key:
            self.cs_release_key = key
            self.cs_release_time = timestamp
            self.cs_press_key = None
            self.cs_press_time = None

    def classify_shot(self, shot_time: float) -> Tuple[str, Optional[float], Optional[float]]:
        """
        Returns a 3-tuple:
          ("Counter-strafe", cs_time_ms, shot_delay_ms)
          ("Overlap",        overlap_time_ms, None)
          ("Bad",            None, None)
        """
        if self.overlap_start_time is not None:
            if not (
                self.cs_press_time is not None
                and self.cs_release_time is not None
                and self.cs_release_time > self.overlap_start_time
                and self.cs_press_time > self.cs_release_time
            ):
                overlap_time = shot_time - self.overlap_start_time
                self._reset()
                return "Overlap", overlap_time, None

        if (
            self.cs_press_time is not None
            and self.cs_release_time is not None
            and self.cs_press_time > self.cs_release_time
        ):
            cs_time = self.cs_press_time - self.cs_release_time
            shot_delay = shot_time - self.cs_press_time
            self._reset()
            return "Counter-strafe", cs_time, shot_delay

        if self.held_keys:
            reason = "still moving"
        elif self.cs_release_key is not None:
            reason = "no counter-press"
        else:
            reason = "no movement"
        self._reset()
        return "Bad", None, reason

    def _reset(self) -> None:
        self.cs_release_key = None
        self.cs_release_time = None
        self.cs_press_key = None
        self.cs_press_time = None
        self.overlap_start_time = None
        self.micro_candidate_duration = None
