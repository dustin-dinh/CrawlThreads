import json
from pathlib import Path

from app.core.config import ROOT_DIR
from .base import SearchOptions, SourceAdapter, StoryPayload
from .threads import _parse_datetime


class DemoSource(SourceAdapter):
    slug = "demo"

    @property
    def configured(self) -> bool:
        return True

    async def search(self, query: str, options: SearchOptions) -> list[StoryPayload]:
        data = json.loads((ROOT_DIR / "data" / "demo" / "stories.json").read_text(encoding="utf-8"))
        terms = [part.strip().lower() for part in query.split("+") if part.strip()]
        ranked = []
        for item in data:
            haystack = f"{item['title']} {item['text']} {' '.join(item.get('tags', []))}".lower()
            matches = sum(term in haystack for term in terms)
            if matches or not terms:
                ranked.append((matches, item))
        ranked.sort(key=lambda pair: pair[0], reverse=True)
        selected = [item for _, item in ranked[: options.limit]]
        if not selected:
            selected = data[: min(options.limit, 3)]
        return [StoryPayload(
            external_id=f"demo-{item['id']}-{abs(hash(query)) % 100000}",
            source=self.slug,
            source_url=item["source_url"],
            author=item.get("author"),
            author_url=item.get("author_url"),
            text=item["text"],
            title=item["title"],
            created_at=_parse_datetime(item.get("created_at")),
            language=item.get("language", "vi"),
            query=query,
            tags=item.get("tags", []),
            reply_count=item.get("reply_count"),
            like_count=item.get("like_count"),
            media_type=item.get("media_type"),
            metadata={"notice": "Dữ liệu giả lập để đánh giá giao diện; không phải nguồn thật."},
            is_demo=True,
        ) for item in selected]
