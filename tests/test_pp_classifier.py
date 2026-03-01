"""
Tests for ppClassifier — AxisState, ShotClassification, MovementClassifier.

All timestamps are in milliseconds.
"""

import pytest
from classifier.ppClassifier import AxisState, MovementClassifier, ShotClassification


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

    def test_release_of_initial_key_clears_cs_press_fields(self):
        # Releasing the initial key (not the CS key) should clear cs_press fields
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 150.0)
        ax.on_press("D", 160.0)    # sets cs_press fields
        ax.on_release("A", 200.0)  # releasing A (not the CS key) should reset state
        assert ax.cs_press_key is None
        assert ax.cs_press_time is None

    def test_release_of_cs_key_preserves_cs_press_fields(self):
        # Releasing the counter-press key (D tap) must NOT wipe cs_press fields
        # so that classify_shot can still detect the counter-strafe
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 150.0)
        ax.on_press("D", 160.0)    # sets cs_press fields
        ax.on_release("D", 200.0)  # releasing the CS tap — must preserve state
        assert ax.cs_press_key == "D"
        assert ax.cs_press_time == 160.0

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

    def test_ignore_unknown_key_on_press(self):
        ax = make_axis()
        ax.on_press("X", 100.0)
        assert len(ax.held_keys) == 0

    def test_ignore_unknown_key_on_release(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("X", 200.0)   # should not affect A's held status
        assert "A" in ax.held_keys


# ===========================================================================
# AxisState — overlap detection
# ===========================================================================

class TestAxisStateOverlap:
    def test_overlap_start_set_when_both_keys_held(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 120.0)
        assert ax.overlap_start_time == 120.0

    def test_overlap_start_not_set_when_no_prior_hold(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_release("A", 110.0)
        ax.on_press("D", 120.0)
        assert ax.overlap_start_time is None

    def test_overlap_start_only_set_once(self):
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 120.0)   # overlap starts at 120
        ax.on_press("A", 140.0)   # re-press should not overwrite
        assert ax.overlap_start_time == 120.0


# ===========================================================================
# AxisState.classify_shot — Counter-strafe
# ===========================================================================

class TestClassifyCounterStrafe:
    def _setup_cs(self, release_t=200.0, press_t=250.0) -> AxisState:
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
        ax.on_press("D", 150.0)
        return ax

    def test_overlap_label(self):
        label, _, _ = self._setup_overlap().classify_shot(200.0)
        assert label == "Overlap"

    def test_overlap_time_value(self):
        _, overlap_time, _ = self._setup_overlap().classify_shot(200.0)
        assert overlap_time == pytest.approx(50.0)   # 200 - 150

    def test_overlap_third_element_is_none(self):
        _, _, third = self._setup_overlap().classify_shot(200.0)
        assert third is None

    def test_overlap_resets_state(self):
        ax = self._setup_overlap()
        ax.classify_shot(200.0)
        assert ax.overlap_start_time is None

    def test_cs_after_overlap_escape_is_counter_strafe(self):
        """Releasing one overlapped key and pressing opposite → Counter-strafe."""
        ax = make_axis()
        ax.on_press("A", 100.0)
        ax.on_press("D", 120.0)          # overlap_start_time = 120
        ax.on_release("D", 130.0)        # cs_release_key = D, cs_release_time = 130
        ax.on_press("A", 140.0)          # cs_press_key = A, cs_press_time = 140 > 130
        label, cs_time, _ = ax.classify_shot(200.0)
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

    def test_bad_when_only_one_key_pressed(self):
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
    def test_perfect_display(self):
        sc = ShotClassification(label="Perfect", cs_time=30.0, shot_delay=100.0)
        text = sc.to_display_string()
        assert "Perfect" in text
        assert "CS time: 30 ms" in text
        assert "Shot delay: 100 ms" in text

    def test_good_display(self):
        sc = ShotClassification(label="Good", cs_time=30.0, shot_delay=400.0)
        text = sc.to_display_string()
        assert "Good" in text
        assert "CS time: 30 ms" in text
        assert "Shot delay: 400 ms" in text

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

    def test_bad_display_with_sub_label(self):
        sc = ShotClassification(label="Bad", sub_label="Firing too early")
        text = sc.to_display_string()
        assert "Bad" in text
        assert "Firing too early" in text

    def test_bad_display_shows_overlap_time(self):
        sc = ShotClassification(label="Bad", sub_label="Overlapping movement", overlap_time=55.0)
        text = sc.to_display_string()
        assert "Overlapping movement" in text
        assert "55 ms" in text

    def test_not_detected_display(self):
        sc = ShotClassification(label="Not detected")
        text = sc.to_display_string()
        assert "Not detected" in text


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
# MovementClassifier — Shift / Ctrl tracking
# ===========================================================================

class TestMovementClassifierSpecialKeys:
    def test_shift_held_on_press(self):
        mc = MovementClassifier()
        mc.on_press("SHIFT", 100.0)
        assert mc._shift_held is True

    def test_shift_released(self):
        mc = MovementClassifier()
        mc.on_press("SHIFT", 100.0)
        mc.on_release("SHIFT", 200.0)
        assert mc._shift_held is False

    def test_ctrl_held_on_press(self):
        mc = MovementClassifier()
        mc.on_press("CTRL", 100.0)
        assert mc._ctrl_held is True

    def test_ctrl_released(self):
        mc = MovementClassifier()
        mc.on_press("CTRL", 100.0)
        mc.on_release("CTRL", 200.0)
        assert mc._ctrl_held is False

    def test_shift_not_routed_to_axes(self):
        mc = MovementClassifier()
        mc.on_press("SHIFT", 100.0)
        assert len(mc.vertical.held_keys) == 0
        assert len(mc.horizontal.held_keys) == 0


# ===========================================================================
# MovementClassifier — Not detected
# ===========================================================================

class TestNotDetected:
    def test_no_movement_ever_is_not_detected(self):
        mc = MovementClassifier()
        result = mc.classify_shot(100.0)
        assert result.label == "Not detected"

    def test_movement_outside_500ms_window_is_not_detected(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        result = mc.classify_shot(600.0)   # 600 ms > 500 ms window
        assert result.label == "Not detected"

    def test_movement_within_500ms_window_is_not_not_detected(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        result = mc.classify_shot(400.0)   # 400 ms within window
        assert result.label != "Not detected"

    def test_movement_exactly_at_boundary_is_not_detected(self):
        """shot_time - last_movement_time == 500 is NOT within window (strict >)."""
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        result = mc.classify_shot(500.0)   # exactly 500 ms — not detected
        assert result.label == "Not detected"


# ===========================================================================
# MovementClassifier — axis priority & routing
# ===========================================================================

class TestMovementClassifierPriority:
    def _do_cs(self, mc: MovementClassifier, axis: str, t0: float = 0.0) -> float:
        if axis == "vertical":
            k1, k2 = mc.vertical.keys
        else:
            k1, k2 = mc.horizontal.keys
        mc.on_press(k1, t0)
        mc.on_release(k1, t0 + 100)
        mc.on_press(k2, t0 + 150)
        return t0 + 250

    def _do_overlap(self, mc: MovementClassifier, axis: str, t0: float = 0.0) -> float:
        if axis == "vertical":
            k1, k2 = mc.vertical.keys
        else:
            k1, k2 = mc.horizontal.keys
        mc.on_press(k1, t0)
        mc.on_press(k2, t0 + 20)
        return t0 + 50

    def test_overlap_beats_counter_strafe(self):
        mc = MovementClassifier()
        self._do_cs(mc, "vertical", t0=0.0)
        shot_time = self._do_overlap(mc, "horizontal", t0=0.0)
        result = mc.classify_shot(shot_time)
        # Overlap maps to Bad per spec; must not return Counter-strafe/Perfect/Good
        assert result.label == "Bad"
        assert result.sub_label == "Overlapping movement"

    def test_counter_strafe_beats_bad(self):
        mc = MovementClassifier()
        shot_time = self._do_cs(mc, "vertical", t0=0.0)
        result = mc.classify_shot(shot_time)
        # Should be Perfect or Good (after filter), but not Bad or Not detected
        assert result.label in ("Perfect", "Good")

    def test_both_bad_returns_bad(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)              # movement recorded but no CS
        result = mc.classify_shot(100.0)
        assert result.label == "Bad"

    def test_both_bad_has_no_counter_strafe_sub_label(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        result = mc.classify_shot(100.0)
        assert result.sub_label == "No counter-strafe"

    def test_same_label_tiebreak_by_larger_cs_time(self):
        """When both axes yield Counter-strafe, the one with larger cs_time wins."""
        mc = MovementClassifier()
        # Vertical: cs_time = 70 ms
        mc.on_press("W", 0.0)
        mc.on_release("W", 100.0)
        mc.on_press("S", 170.0)
        # Horizontal: cs_time = 40 ms
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 140.0)
        result = mc.classify_shot(300.0)
        assert result.cs_time == pytest.approx(70.0)   # vertical wins (larger)


# ===========================================================================
# End-to-end scenarios
# ===========================================================================

class TestEndToEnd:
    def test_perfect_counter_strafe(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)        # cs_time = 30 ms
        result = mc.classify_shot(230.0)  # shot_delay = 100 ms → Perfect
        assert result.label == "Perfect"
        assert result.cs_time == pytest.approx(30.0)
        assert result.shot_delay == pytest.approx(100.0)

    def test_good_counter_strafe(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)         # cs_time = 30 ms
        result = mc.classify_shot(530.0)  # shot_delay = 400 ms → Good
        assert result.label == "Good"

    def test_bad_firing_too_early(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)         # cs_time = 30 ms
        result = mc.classify_shot(160.0)  # shot_delay = 30 ms → too early
        assert result.label == "Bad"
        assert result.sub_label == "Firing too early"

    def test_bad_holding_shift(self):
        mc = MovementClassifier()
        mc.on_press("SHIFT", 0.0)
        mc.on_press("A", 10.0)
        mc.on_release("A", 110.0)
        mc.on_press("D", 130.0)
        result = mc.classify_shot(230.0)  # shot_delay = 100 ms → but shift held
        assert result.label == "Bad"
        assert result.sub_label == "Holding Shift"

    def test_bad_holding_ctrl(self):
        mc = MovementClassifier()
        mc.on_press("CTRL", 0.0)
        mc.on_press("A", 10.0)
        mc.on_release("A", 110.0)
        mc.on_press("D", 130.0)
        result = mc.classify_shot(230.0)
        assert result.label == "Bad"
        assert result.sub_label == "Holding Ctrl"

    def test_bad_overlapping_movement(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_press("D", 20.0)    # overlap starts
        result = mc.classify_shot(100.0)
        assert result.label == "Bad"
        assert result.sub_label == "Overlapping movement"
        assert result.overlap_time == pytest.approx(80.0)   # 100 - 20

    def test_not_detected_long_pause(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        result = mc.classify_shot(600.0)   # 600 ms > 500 ms window
        assert result.label == "Not detected"

    def test_multiple_shots_reset_between(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)
        result1 = mc.classify_shot(230.0)
        assert result1.label in ("Perfect", "Good")
        # Second shot: no new CS setup; movement was at t=130, shot at ~400
        result2 = mc.classify_shot(400.0)
        # 400 - 130 = 270 ms which is within 500 ms, so should be Bad (no new CS)
        assert result2.label == "Bad"

    def test_display_string_present_for_perfect(self):
        mc = MovementClassifier()
        mc.on_press("A", 0.0)
        mc.on_release("A", 100.0)
        mc.on_press("D", 130.0)
        result = mc.classify_shot(230.0)
        text = result.to_display_string()
        assert "Perfect" in text
