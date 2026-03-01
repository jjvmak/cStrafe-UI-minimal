import argparse

from classifier import CLASSIFIERS, DebugLogger
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
    parser.add_argument(
        "--debugger",
        nargs="?",
        const=True,
        default=False,
        type=lambda x: x.lower() in ("true", "1", "yes"),
        metavar="true|false",
        help="Enable debug overlay (default: false)",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    MovementClassifier, ShotFilter = CLASSIFIERS[args.classifier]

    forward, backward, left, right = resolve_movement_keys()
    overlay = Overlay(debug_mode=bool(args.debugger))

    debug_logger: DebugLogger | None = None
    if args.debugger:
        debug_logger = DebugLogger(overlay.log_debug)

    classifier = MovementClassifier(
        vertical_keys=(forward, backward),
        horizontal_keys=(left, right),
        debug_logger=debug_logger,
    )
    shot_filter = ShotFilter()
    movement_keys = frozenset((forward, backward, left, right))
    listener = InputListener(overlay, classifier, shot_filter, movement_keys, left_key=left, right_key=right)
    listener.start()
    overlay.run()


if __name__ == "__main__":
    main()
