from .shot_classification import ShotClassification
from ..base import ShotFilterInterface, ShotClassificationInterface


class ShotFilter(ShotFilterInterface):
    """
    Applies ppClassifier-specific threshold rules to a raw ShotClassification.

    Classification logic (all times in ms):
      - Not detected                     → pass through
      - Overlap                          → Bad / "Overlapping movement"
      - Holding Shift or Ctrl            → Bad (sub_label set)
      - shot_delay < MIN_SHOT_DELAY      → Bad / "Firing too early"
      - MIN_SHOT_DELAY <= delay <= 300   → Perfect
      - 300 < delay <= 500               → Good
      - delay > 500                      → Bad
      - otherwise                        → Bad
    """

    MIN_SHOT_DELAY = 80.0       # Minimum ms for a valid (non-early) CS
    PERFECT_MAX = 300.0         # Upper bound (inclusive) for "Perfect"
    GOOD_MAX = 500.0            # Upper bound (inclusive) for "Good"

    def apply(self, raw: ShotClassificationInterface) -> ShotClassification:
        assert isinstance(raw, ShotClassification)

        if raw.label == "Not detected":
            return raw

        if raw.label == "Overlap":
            return ShotClassification(
                label="Bad",
                sub_label="Overlapping movement",
                overlap_time=raw.overlap_time,
            )

        if raw.label == "Counter-strafe":
            cs_time = raw.cs_time
            shot_delay = raw.shot_delay

            if raw.shift_held:
                return ShotClassification(
                    label="Bad",
                    sub_label="Holding Shift",
                    cs_time=cs_time,
                    shot_delay=shot_delay,
                )

            if raw.ctrl_held:
                return ShotClassification(
                    label="Bad",
                    sub_label="Holding Ctrl",
                    cs_time=cs_time,
                    shot_delay=shot_delay,
                )

            if shot_delay is None:
                return ShotClassification(label="Bad")

            if shot_delay < self.MIN_SHOT_DELAY:
                return ShotClassification(
                    label="Bad",
                    sub_label="Firing too early",
                    cs_time=cs_time,
                    shot_delay=shot_delay,
                )

            if self.MIN_SHOT_DELAY <= shot_delay <= self.PERFECT_MAX:
                return ShotClassification(
                    label="Perfect",
                    cs_time=cs_time,
                    shot_delay=shot_delay,
                )

            if self.PERFECT_MAX < shot_delay <= self.GOOD_MAX:
                return ShotClassification(
                    label="Good",
                    cs_time=cs_time,
                    shot_delay=shot_delay,
                )

            # shot_delay > GOOD_MAX (> 500 ms)
            return ShotClassification(label="Bad", sub_label="Fired too late", cs_time=cs_time, shot_delay=shot_delay)

        # "Bad" and any unexpected labels
        return raw
