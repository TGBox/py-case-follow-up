from dataclasses import dataclass, field, asdict
from typing import Any
from constants import DEFAULT_SNIPPET_CATEGORY, VALIDATION_MESSAGES


@dataclass
class Snippet:
    snippet_id: str = ""
    title: str = ""
    category: str = DEFAULT_SNIPPET_CATEGORY
    content: str = ""
    tags: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.snippet_id.strip():
            errors.append(VALIDATION_MESSAGES["snippet_id_required"])
        if not self.title.strip():
            errors.append(VALIDATION_MESSAGES["snippet_title_required"])
        if not self.content.strip():
            errors.append(VALIDATION_MESSAGES["snippet_content_required"])
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snippet":
        return cls(
            snippet_id=data.get("snippet_id", ""),
            title=data.get("title", ""),
            category=data.get("category", DEFAULT_SNIPPET_CATEGORY),
            content=data.get("content", ""),
            tags=list(data.get("tags", [])),
        )
