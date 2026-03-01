from typing import Optional, Tuple

from ..base import ShotClassificationInterface


class ShotClassification(ShotClassificationInterface):
    """
    Represents the classification outcome of a single shot event for ppClassifier.

    Labels after filtering: "Perfect", "Good", "Bad", "Not detected", "Overlap".
    Raw label from axes before filtering: "Counter-strafe", "Overlap", "Bad".

    Attributes:
        label:        Final label after ShotFilter processing.
        cs_time:      Gap between key release and opposite key press (ms).
        shot_delay:   Gap between opposite key press and shot (ms).
        overlap_time: Duration of key overlap before shot (ms).
        sub_label:    Optional fine-grained reason (e.g. "Firing too early").
        shift_held:   Whether left Shift was held at shot time.
        ctrl_held:    Whether left Ctrl was held at shot time.
    """

    def __init__(
        self,
        label: str,
        cs_time: Optional[float] = None,
        shot_delay: Optional[float] = None,
        overlap_time: Optional[float] = None,
        sub_label: Optional[str] = None,
        shift_held: bool = False,
        ctrl_held: bool = False,
    ) -> None:
        self.label = label
        self.cs_time = cs_time
        self.shot_delay = shot_delay
        self.overlap_time = overlap_time
        self.sub_label = sub_label
        self.shift_held = shift_held
        self.ctrl_held = ctrl_held

    def to_display_string(self) -> str:
        if self.label in ("Perfect", "Good"):
            lines = [f"Classification: {self.label}"]
            if self.cs_time is not None:
                lines.append(f"CS time: {self.cs_time:.0f} ms")
            if self.shot_delay is not None:
                lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
            return "\n".join(lines)

        if self.label == "Counter-strafe":
            lines = ["Classification: Counter-strafe"]
            if self.cs_time is not None:
                lines.append(f"CS time: {self.cs_time:.0f} ms")
            if self.shot_delay is not None:
                lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
            return "\n".join(lines)

        if self.label == "Overlap":
            lines = ["Classification: Overlap"]
            if self.overlap_time is not None:
                lines.append(f"Overlap: {self.overlap_time:.0f} ms")
            return "\n".join(lines)

        if self.label == "Not detected":
            return "Classification: Not detected"

        # Bad — with or without timing
        lines = ["Classification: Bad"]
        if self.sub_label:
            lines.append(self.sub_label)
        if self.overlap_time is not None:
            lines.append(f"Overlap: {self.overlap_time:.0f} ms")
        if self.cs_time is not None and self.shot_delay is not None:
            lines.append(f"CS time: {self.cs_time:.0f} ms")
            lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
        return "\n".join(lines)

    @classmethod
    def from_axis_results(
        cls,
        h_result: Tuple,
        v_result: Tuple,
        shift_held: bool = False,
        ctrl_held: bool = False,
    ) -> "ShotClassification":
        """
        Merge two axis 3-tuples into a single raw ShotClassification.
        Priority: Overlap > Counter-strafe (larger cs_time wins tie) > Bad.
        """
        results = [h_result, v_result]

        overlap_results = [r for r in results if r[0] == "Overlap"]
        if overlap_results:
            best = max(overlap_results, key=lambda r: r[1] if r[1] is not None else 0.0)
            return cls(
                label="Overlap",
                overlap_time=best[1],
                shift_held=shift_held,
                ctrl_held=ctrl_held,
            )

        cs_results = [r for r in results if r[0] == "Counter-strafe"]
        if cs_results:
            # Larger cs_time wins the tie-break (most conservative / worst CS)
            best = max(cs_results, key=lambda r: r[1] if r[1] is not None else 0.0)
            return cls(
                label="Counter-strafe",
                cs_time=best[1],
                shot_delay=best[2],
                shift_held=shift_held,
                ctrl_held=ctrl_held,
            )

        return cls(label="Bad", shift_held=shift_held, ctrl_held=ctrl_held)
