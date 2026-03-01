"""
Tests for ppClassifier ShotFilter.apply().

Covers:
  - Not detected passes through unchanged
  - Overlap → Bad / "Overlapping movement"
  - Counter-strafe: Perfect (80–300 ms), Good (300–500 ms)
  - Counter-strafe: Bad — firing too early (<80 ms)
  - Counter-strafe: Bad — shot_delay exceeds hard limit (>230 ms)
  - Counter-strafe: Bad — combined cs_time + shot_delay > 430 ms
  - Counter-strafe: Bad — Holding Shift
  - Counter-strafe: Bad — Holding Ctrl
  - Counter-strafe: Bad — missing timing fields
  - Boundary values are not rejected
  - Bad raw passes through unchanged
  - Return type is always ShotClassification
"""

import pytest
from classifier.ppClassifier import ShotClassification, ShotFilter


# ===========================================================================
# Not detected
# ===========================================================================

class TestShotFilterNotDetected:
    def test_not_detected_passes_through(self):
        f = ShotFilter()
        raw = ShotClassification(label="Not detected")
        assert f.apply(raw).label == "Not detected"


# ===========================================================================
# Overlap
# ===========================================================================

class TestShotFilterOverlap:
    def test_overlap_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Overlap", overlap_time=50.0)
        result = f.apply(raw)
        assert result.label == "Bad"

    def test_overlap_sub_label_is_overlapping_movement(self):
        f = ShotFilter()
        raw = ShotClassification(label="Overlap", overlap_time=50.0)
        assert f.apply(raw).sub_label == "Overlapping movement"

    def test_overlap_time_preserved(self):
        f = ShotFilter()
        raw = ShotClassification(label="Overlap", overlap_time=42.5)
        assert f.apply(raw).overlap_time == pytest.approx(42.5)


# ===========================================================================
# Counter-strafe — Perfect
# ===========================================================================

class TestShotFilterPerfect:
    def test_shot_delay_at_min_boundary_is_perfect(self):
        """shot_delay == 80 ms → Perfect (inclusive lower bound)."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=80.0)
        assert f.apply(raw).label == "Perfect"

    def test_shot_delay_in_range_is_perfect(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=150.0)
        assert f.apply(raw).label == "Perfect"

    def test_shot_delay_at_perfect_max_boundary_is_perfect(self):
        """shot_delay == 300 ms → Perfect (inclusive upper bound)."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=300.0)
        assert f.apply(raw).label == "Perfect"

    def test_perfect_preserves_cs_time(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=25.0, shot_delay=100.0)
        assert f.apply(raw).cs_time == pytest.approx(25.0)

    def test_perfect_preserves_shot_delay(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=25.0, shot_delay=100.0)
        assert f.apply(raw).shot_delay == pytest.approx(100.0)


# ===========================================================================
# Counter-strafe — Good
# ===========================================================================

class TestShotFilterGood:
    def test_shot_delay_just_above_perfect_is_good(self):
        """shot_delay == 301 ms → Good."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=301.0)
        assert f.apply(raw).label == "Good"

    def test_shot_delay_in_good_range(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=400.0)
        assert f.apply(raw).label == "Good"

    def test_good_preserves_timing(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=20.0, shot_delay=350.0)
        result = f.apply(raw)
        assert result.cs_time == pytest.approx(20.0)
        assert result.shot_delay == pytest.approx(350.0)


# ===========================================================================
# Counter-strafe — Bad (firing too early)
# ===========================================================================

class TestShotFilterFiringTooEarly:
    def test_shot_delay_below_80_is_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=50.0)
        assert f.apply(raw).label == "Bad"

    def test_firing_too_early_sub_label(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=50.0)
        result = f.apply(raw)
        assert result.sub_label == "Firing too early"

    def test_shot_delay_zero_is_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=0.0)
        assert f.apply(raw).label == "Bad"

    def test_shot_delay_79_is_bad(self):
        """79 ms is below the 80 ms minimum."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=79.0)
        assert f.apply(raw).label == "Bad"

    def test_timing_preserved_on_early_shot(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=50.0)
        result = f.apply(raw)
        assert result.cs_time == pytest.approx(30.0)
        assert result.shot_delay == pytest.approx(50.0)


# ===========================================================================
# Counter-strafe — Bad (shot_delay beyond Good max)
# ===========================================================================

class TestShotFilterGoodMaxBoundary:
    def test_shot_delay_at_good_max_is_good(self):
        """shot_delay == 500 ms (cs_time=None bypasses combined check) → Good."""
        f = ShotFilter()
        # cs_time=None skips the combined threshold; shot_delay=500 falls in Good range
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=500.0)
        assert f.apply(raw).label == "Good"

    def test_shot_delay_in_good_range_small_cs_time(self):
        """cs_time=20 + shot_delay=400 = 420 <= 430 combined → Good."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=20.0, shot_delay=400.0)
        assert f.apply(raw).label == "Good"

    def test_shot_delay_above_good_max_is_bad(self):
        """shot_delay == 501 ms (cs_time=None) → Bad (beyond Good range)."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=501.0)
        assert f.apply(raw).label == "Bad"

    def test_fired_too_late_sub_label(self):
        """shot_delay beyond Good max → sub_label 'Fired too late'."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=501.0)
        assert f.apply(raw).sub_label == "Fired too late"

    def test_timing_preserved_on_too_late_shot(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=550.0)
        result = f.apply(raw)
        assert result.cs_time is None
        assert result.shot_delay == pytest.approx(550.0)


# ===========================================================================
# Counter-strafe — Bad (combined threshold)
# ===========================================================================

class TestShotFilterCombinedThreshold:
    def test_combined_at_boundary_is_not_rejected(self):
        """cs_time + shot_delay == 430 is at the boundary — not rejected."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=215.0, shot_delay=215.0)
        # shot_delay=215 is within Perfect range (80–300), combined=430 → accepted
        assert f.apply(raw).label in ("Perfect", "Good")

    def test_combined_just_above_threshold_is_bad(self):
        """cs_time + shot_delay == 431 → Bad."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=216.0, shot_delay=215.0)
        assert f.apply(raw).label == "Bad"

    def test_combined_threshold_sub_label(self):
        """cs_time + shot_delay above threshold → sub_label 'CS too slow'."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=216.0, shot_delay=215.0)
        assert f.apply(raw).sub_label == "CS too slow"

    def test_high_cs_time_with_low_shot_delay_not_rejected(self):
        """Large cs_time is fine as long as combined stays within threshold."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=200.0, shot_delay=100.0)
        # combined = 300 ≤ 430 → accepted
        assert f.apply(raw).label in ("Perfect", "Good")


# ===========================================================================
# Counter-strafe — Bad (holding Shift / Ctrl)
# ===========================================================================

class TestShotFilterSpecialKeys:
    def test_shift_held_is_bad(self):
        f = ShotFilter()
        raw = ShotClassification(
            label="Counter-strafe", cs_time=30.0, shot_delay=100.0, shift_held=True
        )
        assert f.apply(raw).label == "Bad"

    def test_shift_held_sub_label(self):
        f = ShotFilter()
        raw = ShotClassification(
            label="Counter-strafe", cs_time=30.0, shot_delay=100.0, shift_held=True
        )
        assert f.apply(raw).sub_label == "Holding Shift"

    def test_ctrl_held_is_bad(self):
        f = ShotFilter()
        raw = ShotClassification(
            label="Counter-strafe", cs_time=30.0, shot_delay=100.0, ctrl_held=True
        )
        assert f.apply(raw).label == "Bad"

    def test_ctrl_held_sub_label(self):
        f = ShotFilter()
        raw = ShotClassification(
            label="Counter-strafe", cs_time=30.0, shot_delay=100.0, ctrl_held=True
        )
        assert f.apply(raw).sub_label == "Holding Ctrl"

    def test_shift_checked_before_delay(self):
        """Shift takes precedence even when shot_delay would also be bad."""
        f = ShotFilter()
        raw = ShotClassification(
            label="Counter-strafe", cs_time=30.0, shot_delay=50.0, shift_held=True
        )
        assert f.apply(raw).sub_label == "Holding Shift"

    def test_timing_preserved_on_shift_bad(self):
        f = ShotFilter()
        raw = ShotClassification(
            label="Counter-strafe", cs_time=30.0, shot_delay=100.0, shift_held=True
        )
        result = f.apply(raw)
        assert result.cs_time == pytest.approx(30.0)
        assert result.shot_delay == pytest.approx(100.0)


# ===========================================================================
# Counter-strafe — Bad (missing timing fields)
# ===========================================================================

class TestShotFilterMissingFields:
    def test_missing_shot_delay_is_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=None)
        assert f.apply(raw).label == "Bad"

    def test_none_cs_time_does_not_crash(self):
        """None cs_time with valid shot_delay should still classify correctly."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=100.0)
        # combined check is skipped when cs_time is None — shot_delay=100 → Perfect
        assert f.apply(raw).label == "Perfect"


# ===========================================================================
# Bad raw passes through
# ===========================================================================

class TestShotFilterBad:
    def test_bad_passes_through(self):
        f = ShotFilter()
        raw = ShotClassification(label="Bad")
        assert f.apply(raw).label == "Bad"

    def test_bad_with_sub_label_preserved(self):
        f = ShotFilter()
        raw = ShotClassification(label="Bad", sub_label="No counter-strafe")
        result = f.apply(raw)
        assert result.label == "Bad"
        assert result.sub_label == "No counter-strafe"


# ===========================================================================
# Return type
# ===========================================================================

class TestShotFilterReturnType:
    def test_result_is_shot_classification(self):
        f = ShotFilter()
        cases = [
            ShotClassification(label="Not detected"),
            ShotClassification(label="Overlap", overlap_time=20.0),
            ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=100.0),
            ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=50.0),
            ShotClassification(label="Counter-strafe", cs_time=30.0, shot_delay=400.0),
            ShotClassification(label="Bad"),
        ]
        for raw in cases:
            assert isinstance(f.apply(raw), ShotClassification)
