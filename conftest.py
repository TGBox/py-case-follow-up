import sys
from pathlib import Path

# Ensure src directory is in sys.path for test discovery
src_dir = Path(__file__).parent.resolve() / "src"
if str(src_dir) not in sys.path:
    sys.path.insert(0, str(src_dir))
