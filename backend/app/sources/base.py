from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any


class SourceError(RuntimeError):
    pass


@dataclass
class SearchOptions:
    search_type: str = "RECENT"
    since: datetime | None = None
    until: datetime | None = None
    limit: int = 25
    after: str | None = None


@dataclass
class StoryPayload:
    external_id: str
    source: str
    source_url: str
    text: str
    title: str
    author: str | None = None
    author_url: str | None = None
    created_at: datetime | None = None
    language: str | None = None
    query: str = ""
    tags: list[str] = field(default_factory=list)
    reply_count: int | None = None
    like_count: int | None = None
    share_count: int | None = None
    view_count: int | None = None
    media_type: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)
    is_demo: bool = False


class SourceAdapter(ABC):
    slug: str

    @property
    @abstractmethod
    def configured(self) -> bool: ...

    @abstractmethod
    async def search(self, query: str, options: SearchOptions) -> list[StoryPayload]: ...

