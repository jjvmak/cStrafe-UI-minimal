# ppClassifier
This is a custom classifier that implements the same [base](src/classifier/base.py) as the `cs2KitchenClassifier`. The main difference is that the `ppClassifier` classifies counter-strafes as: success, bad, and not detected.

## Classification
This section explains how the `ppClassifier` detects counter-strafes.

### Success
This section describes what is considered a successful counter-strafe.

- **Perfect**: The player moves left (`A`), quickly releases the movement key, and taps the opposite movement key (`D`) to cause a full stop. The player fires (mouse-1) after 80 ms. The acceptable firing delay ranges from 80 ms to 300 ms. The same applies when moving right and stopping by tapping `A`.

- **Good**: The player performs the same sequence but fires later; the acceptable firing delay ranges from 300 ms to 500 ms.

### Bad
This section describes what is considered a bad counter-strafe.

- **Firing too early**: The player completes the counter-strafe but fires before 80 ms.

- **No counter-strafe**: The player moves in any direction (`W`, `A`, `S`, `D`) without performing a counter-strafe (tapping the opposite movement key) and fires (mouse-1).

- **Overlapping movement**: The player presses the opposite movement key without releasing the initial key, then fires (mouse-1). In this scenario, a full stop does not occur.

- **Holding left Shift**: Performing a counter-strafe while holding the left Shift key and firing is labeled **bad**.

- **Holding left Ctrl**: Performing a counter-strafe while holding the left Ctrl key and firing is labeled **bad**.

### Not detected
These occurrences are labeled "not detected" when the player fires but no movement was detected in the 500 ms before firing.

