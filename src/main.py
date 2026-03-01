import argparse

from classifier import CLASSIFIERS
from input_events import InputListener
from key_config import resolve_movement_keys
from overlay import Overlay


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="cStrafe UI")
    parser.add_argument(
        "--classifier",
        choices=list(CLASSIFIERS),
        default="cs2kitchen",
        help="Classifier to use (default: cs2kitchen)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    MovementClassifier, ShotFilter = CLASSIFIERS[args.classifier]

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
