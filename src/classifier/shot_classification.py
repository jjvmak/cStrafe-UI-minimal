from dataclasses import dataclass
from typing import Optional
from .base import ShotClassificationInterface


@dataclass
class ShotClassification(ShotClassificationInterface):
    label: str
    cs_time: Optional[float] = None
    shot_delay: Optional[float] = None
    overlap_time: Optional[float] = None

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
