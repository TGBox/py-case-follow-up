import os
import sys
from pathlib import Path
import pytest

# Ensure src directory is in sys.path for test discovery
src_dir = str(Path(__file__).parent.parent / "src")
if src_dir not in sys.path:
    sys.path.insert(0, src_dir)


@pytest.fixture(autouse=True)
def isolate_global_supportcockpit_config(tmp_path: Path, monkeypatch: pytest.MonkeyPatch):
    """Ensures test runs never overwrite the user's real APPDATA user_config.json."""
    fake_config_dir = tmp_path / "global_config_mock"
    fake_config_dir.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("SUPPORTCOCKPIT_CONFIG_DIR", str(fake_config_dir))
