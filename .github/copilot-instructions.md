# Project
This is a Python 3.13 tool that helps Counter-Strike 2 players practice counter-strafing mechanics. It listens to your movement keys (W, A, S and D) and the left mouse button to determine whether you fired while coming to a full stop, started moving the other way, or were still overlapping directions. The tool provides real-time feedback on your strafing performance, allowing you to improve your movement and shooting accuracy in the game.

## Tecnologies Used
- Python 3.13
- pynput (for listening to keyboard and mouse events)
- tkinter (for creating the overlay UI)

## Venv
Always use 'cstrafe' venv when working on this project.

## Testing
This project uses pytest for testing. We do not want to test any of the UI code or the actual key listening code. Only the logic that determines the classification should be tested. 

## Counter-strafing Mechanics
Counter-strafing is a technique used in first-person shooter games like Counter-Strike to quickly change direction while maintaining accuracy. It involves releasing one movement key and quickly pressing the opposite key before shooting. This allows players to stop their movement momentarily, which will improve shooting accuracy. Optimal counter-strafing requires precise timing, as the shot should be fired within a short delay (80ms) after pressing the opposite key. Overlapping movement (holding both opposing keys at the same time) should be avoided, as it will lead to inaccurate shots.