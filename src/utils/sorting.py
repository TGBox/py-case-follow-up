"""Alphabetical order for user-visible name lists (tags, Programmbereiche)."""

from collections.abc import Iterable

#: Umlauts sort like their base letter (DIN 5007-1: "Ärzte" next to "Arzt",
#: not after "Zahn" as a plain code-point sort would put it).
_FOLD = str.maketrans({"ä": "a", "ö": "o", "ü": "u", "ß": "ss"})


def alpha_key(text: str) -> tuple[str, str]:
    """Case- and umlaut-insensitive sort key; ties keep a stable, defined order."""
    folded = (text or "").casefold().translate(_FOLD)
    return folded, text or ""


def alpha_sorted(items: Iterable[str]) -> list[str]:
    """``items`` as a new list in alphabetical order."""
    return sorted(items, key=alpha_key)
