from classifier import MovementClassifier, ShotFilter
from input_events import InputListener
from key_config import resolve_movement_keys
from overlay import Overlay


def main() -> None:
    forward, backward, left, right = resolve_movement_keys()
    classifier = MovementClassifier(
        vertical_keys=(forward, backward),
        horizontal_keys=(left, right),
    )
    shot_filter = ShotFilter()
    movement_keys = frozenset((forward, backward, left, right))
    overlay = Overlay()
    listener = InputListener(overlay, classifier, shot_filter, movement_keys)
    listener.start()
    overlay.run()


if __name__ == "__main__":
    main()
