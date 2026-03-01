# Project
This is a Python 3.13 tool that helps Counter-Strike 2 players practice counter-strafing mechanics. It listens to the movement keys (W, A, S, D) and the left mouse button to determine whether a shot was fired while coming to a full stop, after starting to move the other way, or while opposing directions were still overlapping. The tool provides real-time feedback on strafing performance so players can improve their movement and shooting accuracy.

## Technologies
- Python 3.13
- pynput (for listening to keyboard and mouse events)
- tkinter (for creating the overlay UI)

## Virtual environment
Always use the `cstrafe` virtual environment when working on this project.

## Testing
This project uses `pytest` for testing. Do not test any of the UI code or the actual key-listening code; only test the logic that determines shot classification.

## Counter-strafing mechanics
Counter-strafing is a technique used in first-person shooters like Counter-Strike to quickly change direction while maintaining accuracy. It involves releasing one movement key and quickly pressing the opposite key before shooting. This briefly stops player movement and can improve shooting accuracy. Optimal counter-strafing requires precise timing: the shot should be fired within a short delay (80 ms) after pressing the opposite key. Avoid overlapping movement (holding both opposing keys simultaneously), as it produces inaccurate shots.