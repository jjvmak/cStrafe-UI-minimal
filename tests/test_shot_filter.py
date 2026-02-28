"""
Tests for ShotFilter.apply()

Covers every branch in the threshold logic:
  - Overlap passes through unchanged
  - Counter-strafe: accepted, rejected by shot_delay threshold,
    rejected by combined cs_time+shot_delay threshold, missing timing fields
  - Any other raw label → Bad
  - Custom threshold values are respected
  - Boundary values (== threshold) are not rejected
  - Return type is always ShotClassification
"""

import pytest
from classifier import ShotClassification, ShotFilter


# ===========================================================================
# Overlap
# ===========================================================================

class TestShotFilterOverlap:
    def test_overlap_passes_through(self):
        f = ShotFilter()
        raw = ShotClassification(label="Overlap", overlap_time=35.0)
        result = f.apply(raw)
        assert result.label == "Overlap"

    def test_overlap_time_preserved(self):
        f = ShotFilter()
        raw = ShotClassification(label="Overlap", overlap_time=42.5)
        result = f.apply(raw)
        assert result.overlap_time == pytest.approx(42.5)

    def test_overlap_with_none_overlap_time(self):
        f = ShotFilter()
        raw = ShotClassification(label="Overlap", overlap_time=None)
        result = f.apply(raw)
        assert result.label == "Overlap"
        assert result.overlap_time is None


# ===========================================================================
# Counter-strafe — accepted
# ===========================================================================

class TestShotFilterCounterStrafeAccepted:
    def test_good_timing_stays_counter_strafe(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=100.0, shot_delay=100.0)
        assert f.apply(raw).label == "Counter-strafe"

    def test_cs_time_preserved_on_accept(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=80.0, shot_delay=90.0)
        result = f.apply(raw)
        assert result.cs_time == pytest.approx(80.0)

    def test_shot_delay_preserved_on_accept(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=80.0, shot_delay=90.0)
        result = f.apply(raw)
        assert result.shot_delay == pytest.approx(90.0)

    def test_shot_delay_at_exact_threshold_is_accepted(self):
        """shot_delay == 230.0 must NOT be rejected (threshold is strict >)."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=230.0)
        assert f.apply(raw).label == "Counter-strafe"

    def test_combined_threshold_both_at_boundary_is_accepted(self):
        """cs_time == 215.0 and shot_delay == 215.0 must NOT be rejected."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=215.0, shot_delay=215.0)
        assert f.apply(raw).label == "Counter-strafe"

    def test_high_cs_time_alone_does_not_reject(self):
        """cs_time > 215 but shot_delay <= 215 → still accepted."""
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=220.0, shot_delay=100.0)
        assert f.apply(raw).label == "Counter-strafe"


# ===========================================================================
# Counter-strafe — rejected
# ===========================================================================

class TestShotFilterCounterStrafeRejected:
    def test_slow_shot_delay_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=231.0)
        assert f.apply(raw).label == "Bad"

    def test_combined_threshold_both_exceeded_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=216.0, shot_delay=216.0)
        assert f.apply(raw).label == "Bad"

    def test_timing_preserved_on_reject(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=250.0)
        result = f.apply(raw)
        assert result.cs_time == pytest.approx(50.0)
        assert result.shot_delay == pytest.approx(250.0)

    def test_missing_cs_time_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=100.0)
        assert f.apply(raw).label == "Bad"

    def test_missing_shot_delay_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=100.0, shot_delay=None)
        assert f.apply(raw).label == "Bad"

    def test_both_timing_fields_missing_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Counter-strafe", cs_time=None, shot_delay=None)
        assert f.apply(raw).label == "Bad"


# ===========================================================================
# Other raw labels
# ===========================================================================

class TestShotFilterOtherLabels:
    def test_bad_raw_stays_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Bad")
        assert f.apply(raw).label == "Bad"

    def test_unknown_label_becomes_bad(self):
        f = ShotFilter()
        raw = ShotClassification(label="Unknown")
        assert f.apply(raw).label == "Bad"


# ===========================================================================
# Custom thresholds
# ===========================================================================

class TestShotFilterCustomThresholds:
    def test_custom_max_shot_delay_respected(self):
        f = ShotFilter(max_shot_delay_ms=100.0)
        accepted = ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=99.0)
        rejected = ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=101.0)
        assert f.apply(accepted).label == "Counter-strafe"
        assert f.apply(rejected).label == "Bad"

    def test_custom_combined_threshold_respected(self):
        f = ShotFilter(max_cs_time_and_delay_ms=50.0)
        accepted = ShotClassification(label="Counter-strafe", cs_time=51.0, shot_delay=49.0)
        rejected = ShotClassification(label="Counter-strafe", cs_time=51.0, shot_delay=51.0)
        assert f.apply(accepted).label == "Counter-strafe"
        assert f.apply(rejected).label == "Bad"


# ===========================================================================
# Return type
# ===========================================================================

class TestShotFilterReturnType:
    def test_result_is_shot_classification(self):
        f = ShotFilter()
        for raw in [
            ShotClassification(label="Overlap", overlap_time=10.0),
            ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=50.0),
            ShotClassification(label="Counter-strafe", cs_time=50.0, shot_delay=300.0),
            ShotClassification(label="Bad"),
        ]:
            assert isinstance(f.apply(raw), ShotClassification)
