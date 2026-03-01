from typing import Optional
from ..base import ShotClassificationInterface


class ShotClassification(ShotClassificationInterface):
    def __init__(
        self,
        label: str,
        cs_time: Optional[float] = None,
        shot_delay: Optional[float] = None,
        overlap_time: Optional[float] = None,
    ):
        self.label: str = label
        self.cs_time: Optional[float] = cs_time
        self.shot_delay: Optional[float] = shot_delay
        self.overlap_time: Optional[float] = overlap_time

    def to_display_string(self) -> str:
        lines = [f"Classification: {self.label}"]
        if (
            self.label == "Counter-strafe"
            and self.cs_time is not None
            and self.shot_delay is not None
        ):
            lines.append(f"CS time: {self.cs_time:.0f} ms")
            lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
        elif self.label == "Overlap" and self.overlap_time is not None:
            lines.append(f"Overlap: {self.overlap_time:.0f} ms")
        elif (
            self.label == "Bad"
            and self.cs_time is not None
            and self.shot_delay is not None
        ):
            lines.append(f"CS time: {self.cs_time:.0f} ms")
            lines.append(f"Shot delay: {self.shot_delay:.0f} ms")
        return "\n".join(lines)
