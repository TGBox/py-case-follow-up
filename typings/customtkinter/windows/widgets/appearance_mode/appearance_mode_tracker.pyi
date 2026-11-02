from collections.abc import Callable
from typing import Any

class AppearanceModeTracker:
    @classmethod
    def add(cls, callback: Callable[[str], Any], widget: Any = None) -> None: ...
    @classmethod
    def remove(cls, callback: Callable[[str], Any]) -> None: ...

