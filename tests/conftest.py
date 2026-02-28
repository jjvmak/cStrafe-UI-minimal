import sys
from pathlib import Path

# Ensure the project's `src` directory is on sys.path so imports like
# `from classifier import ...` continue to work after the src-layout change.
ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"
sys.path.insert(0, str(SRC))
