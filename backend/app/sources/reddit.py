from datetime import datetime, timezone

import httpx

from app.core.config import AppConfig, get_config
from .base import SearchOptions, SourceAdapter, SourceError, StoryPayload
from .http import request_with_retry

SUBREDDITS = "nosleep+Paranormal+Ghoststories+creepyencounters+Glitch_in_the_Matrix+LetsNotMeet+UnresolvedMysteries"


class RedditSource(SourceAdapter):
    """Official Reddit OAuth API adapter using application-only credentials."""

    slug = "reddit"

    def __init__(self, config: AppConfig | None = None, client: httpx.AsyncClient | None = None):
        self.config = config or get_config()
        self._client = client

    @property
    def configured(self) -> bool:
        return bool(self.config.reddit_client_id and self.config.reddit_client_secret)

    async def _token(self, client: httpx.AsyncClient) -> str:
        response = await request_with_retry(
            lambda: client.post(
                "https://www.reddit.com/api/v1/access_token",
                auth=(self.config.reddit_client_id, self.config.reddit_client_secret),
                data={"grant_type": "client_credentials"},
                headers={"User-Agent": self.config.reddit_user_agent},
            ),
            self.slug,
        )
        token = response.json().get("access_token")
        if not token:
            raise SourceError("Reddit không trả về access token")
        return token

    async def search(self, query: str, options: SearchOptions) -> list[StoryPayload]:
        if not self.configured:
            raise SourceError("Reddit chưa được cấu hình. Cần REDDIT_CLIENT_ID và REDDIT_CLIENT_SECRET.")
        owns_client = self._client is None
        client = self._client or httpx.AsyncClient(timeout=self.config.request_timeout_seconds)
        try:
            token = await self._token(client)
            params: dict[str, str | int] = {
                "q": query,
                "restrict_sr": "false",
                "sort": "top" if options.search_type == "TOP" else "new",
                "t": "all",
                "limit": min(options.limit, 100),
                "raw_json": 1,
            }
            if options.after:
                params["after"] = options.after
            response = await request_with_retry(
                lambda: client.get(
                    "https://oauth.reddit.com/search",
                    params=params,
                    headers={"Authorization": f"Bearer {token}", "User-Agent": self.config.reddit_user_agent},
                ),
                self.slug,
            )
            body = response.json()
            results = []
            for child in body.get("data", {}).get("children", []):
                item = child.get("data", {})
                text = (item.get("selftext") or item.get("title") or "").strip()
                permalink = item.get("permalink")
                if not text or not permalink:
                    continue
                created = datetime.fromtimestamp(item["created_utc"], tz=timezone.utc) if item.get("created_utc") else None
                results.append(StoryPayload(
                    external_id=item.get("name") or str(item.get("id")),
                    source=self.slug,
                    source_url=f"https://www.reddit.com{permalink}",
                    author=item.get("author"),
                    author_url=f"https://www.reddit.com/user/{item['author']}" if item.get("author") else None,
                    text=text,
                    title=(item.get("title") or text[:120]).strip(),
                    created_at=created,
                    language="en",
                    query=query,
                    tags=[item.get("subreddit_name_prefixed", "")],
                    reply_count=item.get("num_comments"),
                    like_count=item.get("score"),
                    media_type="SELF" if item.get("is_self") else "LINK",
                    metadata={"subreddit": item.get("subreddit"), "over_18": item.get("over_18"), "after": body.get("data", {}).get("after")},
                ))
            return results
        finally:
            if owns_client:
                await client.aclose()

