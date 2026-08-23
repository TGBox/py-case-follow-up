import sys
from pathlib import Path

# Ensure src directory is in sys.path for test discovery
src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)
