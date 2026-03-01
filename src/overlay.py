import time
import tkinter as tk
from typing import Optional

from classifier import ShotClassification

_DEBUG_MAX_LINES = 60


class Overlay:
    def __init__(self, debug_mode: bool = False) -> None:
        self.root = tk.Tk()
        self.root.title("cStrafe UI by CS2Kitchen")
        self.root.overrideredirect(True)
        self.root.attributes("-topmost", True)
        self.frame = tk.Frame(self.root, bd=2, relief="solid")
        self.frame.pack(fill=tk.BOTH, expand=True)
        self.header_font_size = 12
        self.body_font_size = 10
        self.retro_font = "Courier"
        self._debug_mode = debug_mode

        # Grid layout for self.frame children
        self.frame.grid_rowconfigure(2, weight=1)
        self.frame.grid_columnconfigure(0, weight=1)

        # Top bar: brief orange flash when mouse 1 is clicked
        self.top_bar = tk.Frame(self.frame, bg="#ff6600", height=4)
        self.top_bar.grid(row=0, column=0, sticky="ew")
        self.top_bar.grid_remove()

        self.header = tk.Label(
            self.frame,
            text="cStrafe UI",
            fg="white",
            bg="#303030",
            font=(self.retro_font, self.header_font_size, "bold"),
            anchor="center",
        )
        self.header.grid(row=1, column=0, sticky="ew")

        # Inner frame: left bar | body | right bar
        self._inner_frame = tk.Frame(self.frame, bg="#202020")
        self._inner_frame.grid(row=2, column=0, sticky="nsew")
        self._inner_frame.grid_rowconfigure(0, weight=1)
        self._inner_frame.grid_columnconfigure(1, weight=1)

        # Left bar: yellow while left strafe key is held
        self.left_bar = tk.Frame(self._inner_frame, bg="#ffff00", width=6)
        self.left_bar.grid(row=0, column=0, sticky="nsew")
        self.left_bar.grid_remove()

        self.body = tk.Label(
            self._inner_frame,
            text="Waiting for input...",
            fg="white",
            bg="#202020",
            font=(self.retro_font, self.body_font_size),
            justify=tk.CENTER,
            anchor="center",
        )
        self.body.grid(row=0, column=1, sticky="nsew", padx=8, pady=4)

        # Right bar: yellow while right strafe key is held
        self.right_bar = tk.Frame(self._inner_frame, bg="#ffff00", width=6)
        self.right_bar.grid(row=0, column=2, sticky="nsew")
        self.right_bar.grid_remove()

        # Debug panel (row 3) — only created when debug_mode is enabled
        self._debug_text: Optional[tk.Text] = None
        if debug_mode:
            self._build_debug_panel()

        self._offset_x: Optional[int] = None
        self._offset_y: Optional[int] = None
        self.header.bind("<ButtonPress-1>", self._on_mouse_down)
        self.header.bind("<B1-Motion>", self._on_mouse_move)
        self.is_visible = True
        self._last_text: Optional[str] = None
        self._last_bg_colour: Optional[str] = None

    def _build_debug_panel(self) -> None:
        """Create the debug log panel shown below the main body."""
        debug_container = tk.Frame(self.frame, bg="#101010")
        debug_container.grid(row=3, column=0, sticky="ew")
        debug_container.grid_columnconfigure(0, weight=1)

        title = tk.Label(
            debug_container,
            text="\u2500\u2500 DEBUG \u2500\u2500",
            fg="#00cc44",
            bg="#101010",
            font=(self.retro_font, 8, "bold"),
            anchor="w",
        )
        title.grid(row=0, column=0, columnspan=2, sticky="ew", padx=4, pady=(2, 0))

        self._debug_text = tk.Text(
            debug_container,
            fg="#00cc44",
            bg="#101010",
            insertbackground="#00cc44",
            font=(self.retro_font, 8),
            state=tk.NORMAL,
            height=12,
            width=70,
            wrap=tk.NONE,
            bd=0,
            highlightthickness=0,
        )
        # Allow selection and Ctrl+A/C for clipboard; block all other key edits.
        def _block_edit(event: tk.Event) -> Optional[str]:
            if event.state & 0x4 and event.keysym.lower() in ("c", "a"):
                return None  # let Ctrl+C / Ctrl+A through
            return "break"
        self._debug_text.bind("<Key>", _block_edit)
        scrollbar = tk.Scrollbar(
            debug_container,
            orient=tk.VERTICAL,
            command=self._debug_text.yview,
        )
        self._debug_text.configure(yscrollcommand=scrollbar.set)
        self._debug_text.grid(row=1, column=0, sticky="nsew", padx=(4, 0), pady=(0, 4))
        scrollbar.grid(row=1, column=1, sticky="ns", pady=(0, 4))

    def _on_mouse_down(self, event: tk.Event) -> None:
        self._offset_x = event.x
        self._offset_y = event.y

    def _on_mouse_move(self, event: tk.Event) -> None:
        if self._offset_x is not None and self._offset_y is not None:
            x = event.x_root - self._offset_x
            y = event.y_root - self._offset_y
            self.root.geometry(f"+{x}+{y}")

    def update_result(self, classification: ShotClassification) -> None:
        label = classification.label
        lines = [f"Classification: {label}"]
        if label == "Counter-strafe" and classification.cs_time is not None and classification.shot_delay is not None:
            lines.append(f"CS time: {classification.cs_time:.0f} ms")
            lines.append(f"Shot delay: {classification.shot_delay:.0f} ms")
        elif label == "Overlap" and classification.overlap_time is not None:
            lines.append(f"Overlap: {classification.overlap_time:.0f} ms")
        elif label == "Bad" and classification.cs_time is not None and classification.shot_delay is not None:
            lines.append(f"CS time: {classification.cs_time:.0f} ms")
            lines.append(f"Shot delay: {classification.shot_delay:.0f} ms")
        colours = {
            "Counter-strafe": "#228b22",
            "Overlap": "#ff8c00",
            "Bad": "#cc0000",
        }
        bg_colour = colours.get(label, "#202020")
        text = "\n".join(lines)
        if text == self._last_text and bg_colour == self._last_bg_colour:
            return
        self._last_text = text
        self._last_bg_colour = bg_colour
        def apply_update() -> None:
            self.frame.configure(bg=bg_colour)
            self._inner_frame.configure(bg=bg_colour)
            self.body.configure(text=text, bg=bg_colour)
        self.root.after(0, apply_update)

    def run(self) -> None:
        self.root.mainloop()

    def _apply_font_sizes(self) -> None:
        self.header.configure(font=(self.retro_font, self.header_font_size, "bold"))
        self.body.configure(font=(self.retro_font, self.body_font_size))

    def increase_size(self) -> None:
        if self.body_font_size < 24:
            self.body_font_size += 2
            self.header_font_size += 2
            self._apply_font_sizes()

    def decrease_size(self) -> None:
        if self.body_font_size > 8:
            self.body_font_size -= 2
            self.header_font_size = max(10, self.header_font_size - 2)
            self._apply_font_sizes()

    def toggle_visibility(self) -> None:
        def do_toggle() -> None:
            if self.is_visible:
                self.root.withdraw()
            else:
                self.root.deiconify()
            self.is_visible = not self.is_visible
        self.root.after(0, do_toggle)

    def set_left_key_held(self, held: bool) -> None:
        def apply() -> None:
            if held:
                self.left_bar.grid()
            else:
                self.left_bar.grid_remove()
        self.root.after(0, apply)

    def set_right_key_held(self, held: bool) -> None:
        def apply() -> None:
            if held:
                self.right_bar.grid()
            else:
                self.right_bar.grid_remove()
        self.root.after(0, apply)

    def flash_shot(self) -> None:
        def show() -> None:
            self.top_bar.grid()
            self.root.after(150, hide)
        def hide() -> None:
            self.top_bar.grid_remove()
        self.root.after(0, show)

    def terminate(self) -> None:
        self.root.after(0, self.root.destroy)

    def log_debug(self, entry: str) -> None:
        """Append a timestamped line to the debug panel (thread-safe). No-op when debug_mode is off."""
        if not self._debug_mode or self._debug_text is None:
            return
        ts = time.strftime("%H:%M:%S") + f".{int(time.time() * 1000) % 1000:03d}"
        line = f"[{ts}] {entry}"

        def _append() -> None:
            widget = self._debug_text
            if widget is None:
                return
            widget.insert(tk.END, line + "\n")
            # Trim oldest lines when the buffer exceeds the cap
            line_count = int(widget.index(tk.END).split(".")[0]) - 1
            if line_count > _DEBUG_MAX_LINES:
                excess = line_count - _DEBUG_MAX_LINES
                widget.delete("1.0", f"{excess + 1}.0")
            widget.see(tk.END)

        self.root.after(0, _append)
