from dataclasses import dataclass, field, asdict
from typing import Any


@dataclass
class Snippet:
    snippet_id: str = ""
    title: str = ""
    category: str = "Allgemein"
    content: str = ""
    tags: list[str] = field(default_factory=list)

    def validate(self) -> list[str]:
        errors = []
        if not self.snippet_id.strip():
            errors.append("Snippet ID is required.")
        if not self.title.strip():
            errors.append("Snippet title is required.")
        if not self.content.strip():
            errors.append("Snippet content cannot be empty.")
        return errors

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Snippet":
        return cls(
            snippet_id=data.get("snippet_id", ""),
            title=data.get("title", ""),
            category=data.get("category", "Allgemein"),
            content=data.get("content", ""),
            tags=list(data.get("tags", [])),
        )
