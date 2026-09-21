from typing import Any, Tuple, Optional

class Resampling:
    LANCZOS: int
    NEAREST: int
    BILINEAR: int
    BICUBIC: int

class Image:
    width: int
    height: int
    format: Optional[str]
    size: Tuple[int, int]
    Image: Any
    Resampling: Any

    @classmethod
    def open(cls, fp: Any, mode: str = ...) -> "Image": ...
    @classmethod
    def new(cls, mode: str, size: Tuple[int, int], color: Any = ...) -> "Image": ...
    def save(self, fp: Any, format: Optional[str] = ..., **kwargs: Any) -> None: ...
    def resize(self, size: Tuple[int, int], resample: int = ...) -> "Image": ...

class ImageDraw:
    ImageDraw: Any
    @classmethod
    def Draw(cls, im: Image, mode: Optional[str] = ...) -> Any: ...

class ImageFont:
    @classmethod
    def load_default(cls) -> Any: ...
    @classmethod
    def truetype(cls, font: Any, size: int = ..., index: int = ..., encoding: str = ..., layout_engine: Any = ...) -> Any: ...

class ImageGrab:
    @classmethod
    def grabclipboard(cls) -> Any: ...

class ImageTk:
    class PhotoImage:
        def __init__(self, image: Any = None, size: Any = None, **kw: Any) -> None: ...
