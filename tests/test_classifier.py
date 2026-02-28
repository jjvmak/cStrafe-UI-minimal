"""
Tests for classifier.py

Covers:
  - AxisState: press/release state tracking, overlap detection, CS detection
  - AxisState.classify_shot: Counter-strafe / Overlap / Bad outcomes
  - ShotClassification.to_display_string: all label branches
  - MovementClassifier: key routing, custom bindings, validation,
    axis-priority logic (Overlap > Counter-strafe > Bad), tie-breaking
"""

import pytest
from classifier import AxisState, MovementClassifier, ShotClassification


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def make_axis(keys=("A", "D")) -> AxisState:
    return AxisState(keys=keys)


# ===========================================================================
# AxisState — press / release state
# ===========================================================================

class TestAxisStateTracking:
    def test_press_adds_to_held_keys(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        assert "A" in ax.held_keys

    def test_release_removes_from_held_keys(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 200.0)
        assert "A" not in ax.held_keys

    def test_release_sets_cs_release_fields(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 150.0)
        assert ax.cs_release_key == "A"
        assert ax.cs_release_time == 150.0

    def test_release_clears_cs_press_fields(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 150.0)
        ax.on_press("D", 160.0)   # sets cs_press fields
        ax.on_release("D", 200.0)
        assert ax.cs_press_key is None
        assert ax.cs_press_time is None

    def test_press_records_press_time(self):
        ax = make_axis()
        ax.on_press("A", 123.456)
        assert ax.press_times["A"] == 123.456

    def test_micro_candidate_set_for_short_press(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 150.0)   # 50 ms < 80 ms threshold
        assert ax.micro_candidate_duration == 50.0

    def test_micro_candidate_not_set_for_long_press(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 200.0)   # 100 ms ≥ 80 ms
        assert ax.micro_candidate_duration is None

    def test_on_press_clears_micro_candidate(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 130.0)   # sets micro_candidate_duration
        ax.on_press("D", 140.0)     # should clear it
        assert ax.micro_candidate_duration is None


# ===========================================================================
# AxisState — overlap detection
# ===========================================================================

class TestAxisStateOverlap:
    def test_overlap_start_time_set_when_both_keys_held(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 120.0)   # A is still held → overlap
        assert ax.overlap_start_time == 120.0

    def test_overlap_start_time_not_set_without_prior_hold(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 110.0)
        ax.on_press("D", 120.0)   # A not held → no overlap
        assert ax.overlap_start_time is None

    def test_overlap_start_time_only_set_once(self):
        """Second simultaneous press must not overwrite the start time."""
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 120.0)   # overlap starts at 120
        ax.on_press("A", 140.0)   # pressing A again — should not update start
        assert ax.overlap_start_time == 120.0


# ===========================================================================
# AxisState.classify_shot — Counter-strafe
# ===========================================================================

class TestClassifyCounterStrafe:
    def _setup_cs(self, release_t=200.0, press_t=250.0) -> AxisState:
        """Press A, release A (cs_release), press D (cs_press)."""
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", release_t)
        ax.on_press("D", press_t)
        return ax

    def test_counter_strafe_label(self):
        ax = self._setup_cs()
        label, _, _ = ax.classify_shot(300.0)
        assert label == "Counter-strafe"

    def test_counter_strafe_cs_time(self):
        ax = self._setup_cs(release_t=200.0, press_t=250.0)
        _, cs_time, _ = ax.classify_shot(300.0)
        assert cs_time == pytest.approx(50.0)

    def test_counter_strafe_shot_delay(self):
        ax = self._setup_cs(release_t=200.0, press_t=250.0)
        _, _, shot_delay = ax.classify_shot(310.0)
        assert shot_delay == pytest.approx(60.0)

    def test_counter_strafe_resets_state(self):
        ax = self._setup_cs()
        ax.classify_shot(300.0)
        assert ax.cs_release_key is None
        assert ax.cs_press_key is None
        assert ax.cs_press_time is None
        assert ax.cs_release_time is None


# ===========================================================================
# AxisState.classify_shot — Overlap
# ===========================================================================

class TestClassifyOverlap:
    def _setup_overlap(self) -> AxisState:
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 150.0)   # overlap starts at 150
        return ax

    def test_overlap_label(self):
        ax = self._setup_overlap()
        label, _, _ = ax.classify_shot(200.0)
        assert label == "Overlap"

    def test_overlap_time_value(self):
        ax = self._setup_overlap()
        _, overlap_time, _ = ax.classify_shot(200.0)
        assert overlap_time == pytest.approx(50.0)   # 200 - 150

    def test_overlap_resets_state(self):
        ax = self._setup_overlap()
        ax.classify_shot(200.0)
        assert ax.overlap_start_time is None

    def test_cs_after_overlap_clears_overlap(self):
        """
        If the player correctly counter-strafes *after* an overlap started
        (releases overlapping key and presses the new one), the overlap path
        is skipped and it becomes a Counter-strafe.
        """
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 120.0)          # overlap_start_time = 120
        ax.on_release("A", 130.0)        # cs_release after overlap
        ax.on_press("D", 130.0)          # re-press — but cs_press_time must be > cs_release
        ax2 = make_axis()
        ax2.on_press("A", 100.0)
        ax2.on_press("D", 120.0)         # overlap_start_time = 120
        ax2.on_release("D", 130.0)       # cs_release_key = D, cs_release_time = 130
        ax2.on_press("A", 140.0)         # cs_press_key = A, cs_press_time = 140 > 130
        label, cs_time, _ = ax2.classify_shot(200.0)
        assert label == "Counter-strafe"
        assert cs_time == pytest.approx(10.0)


# ===========================================================================
# AxisState.classify_shot — Bad
# ===========================================================================

class TestClassifyBad:
    def test_bad_when_no_movement(self):
        ax = make_axis()
        label, v1, v2 = ax.classify_shot(100.0)
        assert label == "Bad"
        assert v1 is None
        assert v2 is None

    def test_bad_when_only_one_key_pressed_no_release(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        label, _, _ = ax.classify_shot(200.0)
        assert label == "Bad"

    def test_reset_called_on_bad(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.classify_shot(200.0)
        assert ax.cs_release_key is None


# ===========================================================================
# ShotClassification.to_display_string
# ===========================================================================

class TestShotClassificationDisplay:
    def test_counter_strafe_display(self):
        sc = ShotClassification(label="Counter-strafe", cs_time=45.0, shot_delay=30.0)
        text = sc.to_display_string()
        assert "Counter-strafe" in text
        assert "CS time: 45 ms" in text
        assert "Shot delay: 30 ms" in text

    def test_overlap_display(self):
        sc = ShotClassification(label="Overlap", overlap_time=80.0)
        text = sc.to_display_string()
        assert "Overlap" in text
        assert "80 ms" in text

    def test_bad_display_no_timing(self):
        sc = ShotClassification(label="Bad")
        text = sc.to_display_string()
        assert "Bad" in text
        assert "CS time" not in text

    def test_bad_display_with_timing(self):
        sc = ShotClassification(label="Bad", cs_time=10.0, shot_delay=5.0)
        text = sc.to_display_string()
        assert "Bad" in text
        assert "CS time: 10 ms" in text
        assert "Shot delay: 5 ms" in text

    def test_counter_strafe_missing_values_no_crash(self):
        sc = ShotClassification(label="Counter-strafe")   # no cs_time / shot_delay
        text = sc.to_display_string()
        assert "Counter-strafe" in text
        assert "CS time" not in text


# ===========================================================================
# MovementClassifier — init & validation
# ===========================================================================

class TestMovementClassifierInit:
    def test_default_keys(self):
        mc = MovementClassifier()
        assert mc.vertical.keys == ("W", "S")
        assert mc.horizontal.keys == ("A", "D")

    def test_custom_keys(self):
        mc = MovementClassifier(vertical_keys=("i", "k"), horizontal_keys=("j", "l"))
        assert mc.vertical.keys == ("I", "K")
        assert mc.horizontal.keys == ("J", "L")

    def test_keys_normalised_to_uppercase(self):
        mc = MovementClassifier(vertical_keys=("w", "s"), horizontal_keys=("a", "d"))
        assert mc.vertical.keys == ("W", "S")
        assert mc.horizontal.keys == ("A", "D")

    def test_duplicate_vertical_keys_raises(self):
        with pytest.raises(ValueError):
            MovementClassifier(vertical_keys=("W", "W"), horizontal_keys=("A", "D"))

    def test_duplicate_horizontal_keys_raises(self):
        with pytest.raises(ValueError):
            MovementClassifier(vertical_keys=("W", "S"), horizontal_keys=("D", "D"))


# ===========================================================================
# MovementClassifier — event routing
# ===========================================================================

class TestMovementClassifierRouting:
    def test_vertical_key_routed_correctly(self):
        mc = MovementClassifier()
        mc.on_press("W", 100.0)
        assert "W" in mc.vertical.held_keys
        assert "W" not in mc.horizontal.held_keys

    def test_horizontal_key_routed_correctly(self):
        mc = MovementClassifier()
        mc.on_press("A", 100.0)
        assert "A" in mc.horizontal.held_keys
        assert "A" not in mc.vertical.held_keys

    def test_irrelevant_key_ignored(self):
        mc = MovementClassifier()
        mc.on_press("X", 100.0)
        assert len(mc.vertical.held_keys) == 0
        assert len(mc.horizontal.held_keys) == 0

    def test_release_routed_to_correct_axis(self):
        mc = MovementClassifier()
        mc.on_press("D", 100.0)
        mc.on_release("D", 200.0)
        assert "D" not in mc.horizontal.held_keys


# ===========================================================================
# MovementClassifier.classify_shot — axis priority
# ===========================================================================

def _do_cs(mc: MovementClassifier, axis: str, t0: float = 0.0) -> float:
    """Perform a clean counter-strafe on the given axis, return shot_time."""
    if axis == "vertical":
        k1, k2 = mc.vertical.keys
    else:
        k1, k2 = mc.horizontal.keys
    mc.on_press(k1, t0)
    mc.on_release(k1, t0 + 100)
    mc.on_press(k2, t0 + 150)
    return t0 + 200


def _do_overlap(mc: MovementClassifier, axis: str, t0: float = 0.0) -> float:
    """Create an overlap on the given axis, return shot_time."""
    if axis == "vertical":
        k1, k2 = mc.vertical.keys
    else:
        k1, k2 = mc.horizontal.keys
    mc.on_press(k1, t0)
    mc.on_press(k2, t0 + 20)
    return t0 + 50


class TestMovementClassifierPriority:
    def test_overlap_beats_counter_strafe(self):
        mc = MovementClassifier()
        _do_cs(mc, "vertical", t0=0.0)
        shot_time = _do_overlap(mc, "horizontal", t0=0.0)
        result = mc.classify_shot(shot_time)
        assert result.label == "Overlap"

    def test_overlap_beats_bad(self):
        mc = MovementClassifier()
        shot_time = _do_overlap(mc, "vertical", t0=0.0)
        result = mc.classify_shot(shot_time)
        assert result.label == "Overlap"

    def test_counter_strafe_beats_bad(self):
        mc = MovementClassifier()
        shot_time = _do_cs(mc, "vertical", t0=0.0)
        result = mc.classify_shot(shot_time)
        assert result.label == "Counter-strafe"

    def test_both_bad_returns_bad(self):
        mc = MovementClassifier()
        result = mc.classify_shot(500.0)
        assert result.label == "Bad"

    def test_same_label_tiebreak_by_larger_val(self):
        mc = MovementClassifier()
        mc.on_press("W", 0.0)
        mc.on_release("W", 100.0)
        mc.on_press("S", 170.0)
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 140.0)
        result = mc.classify_shot(300.0)
        assert result.label == "Counter-strafe"
        assert result.cs_time == pytest.approx(70.0)   # vertical wins

    def test_result_type_is_shot_classification(self):
        mc = MovementClassifier()
        result = mc.classify_shot(100.0)
        assert isinstance(result, ShotClassification)


# ===========================================================================
# End-to-end scenarios
# ===========================================================================

class TestEndToEnd:
    def test_clean_horizontal_counter_strafe(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)   # cs_time = 30 ms
        result = mc.classify_shot(200.0)
        assert result.label == "Counter-strafe"
        assert result.cs_time == pytest.approx(30.0)
        assert result.shot_delay == pytest.approx(70.0)

    def test_clean_vertical_counter_strafe(self):
        mc = MovementClassifier()
        mc.on_press("W", 0.0)
        mc.on_release("W", 100.0)
        mc.on_press("S", 110.0)   # cs_time = 10 ms
        result = mc.classify_shot(180.0)
        assert result.label == "Counter-strafe"
        assert result.cs_time == pytest.approx(10.0)

    def test_overlap_scenario(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_press("D", 20.0)   # overlap starts at 20
        result = mc.classify_shot(100.0)
        assert result.label == "Overlap"
        assert result.overlap_time == pytest.approx(80.0)

    def test_shooting_with_no_movement(self):
        mc = MovementClassifier()
        result = mc.classify_shot(100.0)
        assert result.label == "Bad"

    def test_multiple_shots_state_resets_between_shots(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)
        result1 = mc.classify_shot(200.0)
        assert result1.label == "Counter-strafe"
        result2 = mc.classify_shot(400.0)
        assert result2.label == "Bad"

    def test_display_string_populated_for_counter_strafe(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 150.0)
        result = mc.classify_shot(200.0)
        text = result.to_display_string()
        assert "50 ms" in text   # cs_time
        assert "50 ms" in text   # shot_delay (both happen to be 50 here)
