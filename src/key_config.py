"""Resolve movement key bindings from movement_keys.py with safe fallbacks."""


def resolve_movement_keys() -> tuple[str, str, str, str]:
    """Return (forward, backward, left, right) as single uppercase chars.

    Reads FORWARD/BACKWARD/LEFT/RIGHT from movement_keys.py when available.
    Falls back to E/D/S/F (the file's own defaults) on ImportError, and to
    W/S/A/D if the values cannot be converted to strings at all.
    """
    try:
        from movement_keys import FORWARD, BACKWARD, LEFT, RIGHT  # type: ignore
        forward = str(FORWARD)
        backward = str(BACKWARD)
        left = str(LEFT)
        right = str(RIGHT)
    except ImportError:
        forward, backward, left, right = 'E', 'D', 'S', 'F'
    except Exception:
        forward, backward, left, right = 'W', 'S', 'A', 'D'
    forward = (forward[0] if forward else 'W').upper()
    backward = (backward[0] if backward else 'S').upper()
    left = (left[0] if left else 'A').upper()
    right = (right[0] if right else 'D').upper()
    return forward, backward, left, right
