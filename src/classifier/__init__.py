from .cs2KitchenClassifier.movement_classifier import MovementClassifier as CS2KitchenMovementClassifier
from .cs2KitchenClassifier.shot_classification import ShotClassification
from .cs2KitchenClassifier.axis_state import AxisState
from .cs2KitchenClassifier.shot_filter import ShotFilter as CS2KitchenShotFilter
from .ppClassifier.movement_classifier import MovementClassifier as PPMovementClassifier
from .ppClassifier.shot_filter import ShotFilter as PPShotFilter
from .base import (
    MovementClassifierInterface,
    ShotClassificationInterface,
    ShotFilterInterface,
    AxisStateInterface,
)

# Keep default aliases pointing at cs2KitchenClassifier for backwards-compat.
MovementClassifier = CS2KitchenMovementClassifier
ShotFilter = CS2KitchenShotFilter

CLASSIFIERS: dict[str, tuple[type, type]] = {
    "cs2kitchen": (CS2KitchenMovementClassifier, CS2KitchenShotFilter),
    "pp": (PPMovementClassifier, PPShotFilter),
}

__all__ = [
    "AxisState",
    "MovementClassifier",
    "ShotClassification",
    "ShotFilter",
    "CS2KitchenMovementClassifier",
    "CS2KitchenShotFilter",
    "PPMovementClassifier",
    "PPShotFilter",
    "CLASSIFIERS",
    "MovementClassifierInterface",
    "ShotClassificationInterface",
    "ShotFilterInterface",
    "AxisStateInterface",
]
