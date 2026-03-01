from .shot_classification import ShotClassification
from ..base import ShotClassificationInterface, ShotFilterInterface


class ShotFilter(ShotFilterInterface):
    """Apply timing-threshold rules to a raw ShotClassification.

    This is the only place where "too slow → Bad" policy lives.
    It has no I/O, no threading, and no UI dependency, making it
    straightforward to unit-test in isolation.
    """

    def __init__(
        self,
        max_shot_delay_ms: float = 230.0,
        max_cs_time_and_delay_ms: float = 215.0,
    ) -> None:
        self._max_shot_delay_ms = max_shot_delay_ms
        self._max_cs_time_and_delay_ms = max_cs_time_and_delay_ms

    def apply(self, raw: ShotClassificationInterface) -> ShotClassification:
        assert isinstance(raw, ShotClassification)
        if raw.label == "Overlap":
            return ShotClassification(label="Overlap", overlap_time=raw.overlap_time)
        if raw.label == "Counter-strafe":
            cs_time = raw.cs_time
            shot_delay = raw.shot_delay
            if cs_time is not None and shot_delay is not None:
                if shot_delay > self._max_shot_delay_ms or (
                    cs_time > self._max_cs_time_and_delay_ms
                    and shot_delay > self._max_cs_time_and_delay_ms
                ):
                    return ShotClassification(label="Bad", cs_time=cs_time, shot_delay=shot_delay)
                return ShotClassification(label="Counter-strafe", cs_time=cs_time, shot_delay=shot_delay)
            return ShotClassification(label="Bad")
        return ShotClassification(label="Bad")
