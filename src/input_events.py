import threading
import time
from typing import Optional

from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from overlay import Overlay

from pynput import keyboard, mouse

from classifier import MovementClassifierInterface, ShotFilterInterface


class InputListener:
    def __init__(
        self,
        overlay: "Overlay",
        classifier: MovementClassifierInterface,
        shot_filter: ShotFilterInterface,
        movement_keys: frozenset[str],
        left_key: Optional[str] = None,
        right_key: Optional[str] = None,
    ) -> None:
        self.overlay = overlay
        self.classifier = classifier
        self._shot_filter = shot_filter
        self._movement_keys = movement_keys
        self._left_key = left_key
        self._right_key = right_key
        self._lock = threading.Lock()
        self._keyboard_listener: Optional[keyboard.Listener] = None
        self._mouse_listener: Optional[mouse.Listener] = None
        # Tracks which movement/modifier keys are currently held so that
        # duplicate pynput events (a known Windows hook quirk) are ignored.
        self._held_keys: set[str] = set()

    def start(self) -> None:
        self._keyboard_listener = keyboard.Listener(
            on_press=self._on_key_press,
            on_release=self._on_key_release,
        )
        self._keyboard_listener.start()
        self._mouse_listener = mouse.Listener(
            on_click=self._on_click,
        )
        self._mouse_listener.start()

    def _on_key_press(self, key: keyboard.Key) -> None:
        if key == keyboard.Key.f6:
            self.overlay.toggle_visibility()
            return
        if key == keyboard.Key.f8:
            self.stop()
            self.overlay.terminate()
            return
        char_key: Optional[str] = None
        try:
            char_key = key.char
        except AttributeError:
            char_key = None
        if char_key == "=":
            self.overlay.increase_size()
            return
        if char_key == "-":
            self.overlay.decrease_size()
            return
        timestamp = time.time() * 1000.0
        char: Optional[str] = None
        try:
            char = key.char
        except AttributeError:
            char = None
        # Fallback: on Windows, pynput may report key.char as None for regular
        # letter keys when certain OS quirks occur.  Use the virtual key code
        # (vk) to recover the character so movement keys are never silently
        # dropped.
        if char is None:
            try:
                vk = key.vk  # type: ignore[union-attr]
                if vk is not None and 65 <= vk <= 90:  # A–Z
                    char = chr(vk)
            except AttributeError:
                pass
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            if "SHIFT" not in self._held_keys:
                self._held_keys.add("SHIFT")
                with self._lock:
                    self.classifier.on_press("SHIFT", timestamp)
            return
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            if "CTRL" not in self._held_keys:
                self._held_keys.add("CTRL")
                with self._lock:
                    self.classifier.on_press("CTRL", timestamp)
            return
        if char:
            upper_char = char.upper()
            if upper_char in self._movement_keys:
                if upper_char not in self._held_keys:
                    self._held_keys.add(upper_char)
                    with self._lock:
                        self.classifier.on_press(upper_char, timestamp)
            if upper_char == self._left_key:
                self.overlay.set_left_key_held(True)
            elif upper_char == self._right_key:
                self.overlay.set_right_key_held(True)

    def _on_key_release(self, key: keyboard.Key) -> None:
        timestamp = time.time() * 1000.0
        char: Optional[str] = None
        try:
            char = key.char
        except AttributeError:
            char = None
        # Fallback: on Windows, pynput may report key.char as None for regular
        # letter keys when certain OS quirks occur.  Use the virtual key code
        # (vk) to recover the character so movement keys are never silently
        # dropped and never get stuck in _held_keys.
        if char is None:
            try:
                vk = key.vk  # type: ignore[union-attr]
                if vk is not None and 65 <= vk <= 90:  # A–Z
                    char = chr(vk)
            except AttributeError:
                pass
        if key in (keyboard.Key.shift, keyboard.Key.shift_l, keyboard.Key.shift_r):
            if "SHIFT" in self._held_keys:
                self._held_keys.discard("SHIFT")
                with self._lock:
                    self.classifier.on_release("SHIFT", timestamp)
            return
        if key in (keyboard.Key.ctrl, keyboard.Key.ctrl_l, keyboard.Key.ctrl_r):
            if "CTRL" in self._held_keys:
                self._held_keys.discard("CTRL")
                with self._lock:
                    self.classifier.on_release("CTRL", timestamp)
            return
        if char:
            upper_char = char.upper()
            if upper_char in self._movement_keys:
                if upper_char in self._held_keys:
                    self._held_keys.discard(upper_char)
                    with self._lock:
                        self.classifier.on_release(upper_char, timestamp)
            if upper_char == self._left_key:
                self.overlay.set_left_key_held(False)
            elif upper_char == self._right_key:
                self.overlay.set_right_key_held(False)

    def _on_click(self, x: int, y: int, button: mouse.Button, pressed: bool) -> None:
        if button != mouse.Button.left:
            return
        current_time = time.time() * 1000.0
        if pressed:
            self.overlay.flash_shot()
            with self._lock:
                base_result = self.classifier.classify_shot(current_time)
            final_result = self._shot_filter.apply(base_result)
            self.overlay.update_result(final_result)

    def stop(self) -> None:
        if self._keyboard_listener is not None:
            self._keyboard_listener.stop()
            self._keyboard_listener = None
        if self._mouse_listener is not None:
            self._mouse_listener.stop()
            self._mouse_listener = None


