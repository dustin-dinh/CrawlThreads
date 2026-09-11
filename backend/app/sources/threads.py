from datetime import datetime

import httpx

from app.core.config import AppConfig, get_config
from .base import SearchOptions, SourceAdapter, SourceError, StoryPayload
from .http import request_with_retry


class ThreadsSource(SourceAdapter):
    """Official Meta Threads API keyword search adapter.

    Contract verified against Meta's official Threads Postman collection:
    GET /v1.0/keyword_search with threads_basic + threads_keyword_search.
    """

    slug = "threads"
    fields = "id,media_product_type,media_type,permalink,username,text,timestamp,shortcode,is_quote_post,has_replies"

    def __init__(self, config: AppConfig | None = None, client: httpx.AsyncClient | None = None):
        self.config = config or get_config()
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.config.threads_access_token)

    async def search(self, query: str, options: SearchOptions) -> list[StoryPayload]:
        if not self.configured:
            raise SourceError("Threads chưa được cấu hình. Cần token có quyền threads_basic và threads_keyword_search.")
        params: dict[str, str | int] = {
            "q": query,
            "search_type": options.search_type,
            "search_mode": "KEYWORD",
            "fields": self.fields,
            "limit": min(options.limit, 100),
            "access_token": self.config.threads_access_token,
        }
        if options.since:
            params["since"] = options.since.isoformat()
        if options.until:
            params["until"] = options.until.isoformat()
        if options.after:
            params["after"] = options.after
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.config.request_timeout_seconds)
        try:
            response = await request_with_retry(
                lambda: client.get(f"{self.config.threads_api_base}/keyword_search", params=params),
                self.slug,
            )
            body = response.json()
            results: list[StoryPayload] = []
            for item in body.get("data", []):
                text = (item.get("text") or "").strip()
                if not text or not item.get("id") or not item.get("permalink"):
                    continue
                username = item.get("username")
                results.append(StoryPayload(
                    external_id=str(item["id"]),
                    source=self.slug,
                    source_url=item["permalink"],
                    author=username,
                    author_url=f"https://www.threads.net/@{username}" if username else None,
                    text=text,
                    title=text[:117] + ("…" if len(text) > 117 else ""),
                    created_at=_parse_datetime(item.get("timestamp")),
                    query=query,
                    reply_count=1 if item.get("has_replies") else 0,
                    media_type=item.get("media_type"),
                    metadata={
                        "shortcode": item.get("shortcode"),
                        "is_quote_post": item.get("is_quote_post"),
                        "has_replies": item.get("has_replies"),
                        "paging": body.get("paging", {}),
                    },
                ))
            return results
        finally:
            if owns_client:
                await client.aclose()


def _parse_datetime(value: str | None) -> datetime | None:
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00"))
    except ValueError:
        return None

