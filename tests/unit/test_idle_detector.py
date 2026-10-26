import pytest
from utils.idle_detector import IdleDetector


@pytest.fixture(autouse=True)
def reset_idle_mock():
    IdleDetector.reset_mock()
    yield
    IdleDetector.reset_mock()


def test_idle_detector_mock_seconds():
    IdleDetector.set_mock_state(idle_seconds=120.0, is_locked=False)
    assert IdleDetector.get_idle_seconds() == 120.0
    assert not IdleDetector.is_workstation_locked()
    assert IdleDetector.is_user_idle(idle_threshold_seconds=60.0)
    assert not IdleDetector.is_user_idle(idle_threshold_seconds=300.0)


def test_idle_detector_mock_locked():
    IdleDetector.set_mock_state(idle_seconds=5.0, is_locked=True)
    assert IdleDetector.is_workstation_locked()
    # When locked, user is always considered idle regardless of threshold
    assert IdleDetector.is_user_idle(idle_threshold_seconds=600.0)


def test_idle_detector_negative_clamp():
    IdleDetector.set_mock_state(idle_seconds=-10.0, is_locked=False)
    assert IdleDetector.get_idle_seconds() == 0.0


def test_idle_detector_real_system_call_does_not_crash():
    # Verify that calling real OS methods without mock does not raise exceptions
    seconds = IdleDetector.get_idle_seconds()
    assert isinstance(seconds, float)
    assert seconds >= 0.0

    locked = IdleDetector.is_workstation_locked()
    assert isinstance(locked, bool)

    is_idle = IdleDetector.is_user_idle(300.0)
    assert isinstance(is_idle, bool)
