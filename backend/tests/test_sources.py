import json

import httpx
import pytest

from app.core.config import AppConfig
from app.sources import RedditSource, SearchOptions, ThreadsSource


@pytest.mark.asyncio
async def test_threads_normalization_and_pagination_metadata():
    def handler(request: httpx.Request):
        assert request.url.path.endswith("/keyword_search")
        assert request.url.params["search_type"] == "RECENT"
        assert request.url.params["search_mode"] == "KEYWORD"
        return httpx.Response(200, json={"data":[{"id":"t1","text":"Mình thấy một bóng người","permalink":"https://threads.net/@a/post/x","username":"a","timestamp":"2026-01-02T03:04:05+0000","media_type":"TEXT_POST","has_replies":True}],"paging":{"cursors":{"after":"next"}}})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config=AppConfig(_env_file=None,threads_access_token="secret",threads_api_base="https://graph.threads.net/v1.0")
    try:
        items=await ThreadsSource(config,client).search("bóng người",SearchOptions())
    finally:
        await client.aclose()
    assert items[0].source=="threads"
    assert items[0].reply_count==1
    assert items[0].metadata["paging"]["cursors"]["after"]=="next"


@pytest.mark.asyncio
async def test_reddit_oauth_and_result_normalization():
    calls=[]
    def handler(request:httpx.Request):
        calls.append(request.url.path)
        if request.url.path=="/api/v1/access_token":return httpx.Response(200,json={"access_token":"token"})
        assert request.headers["authorization"]=="Bearer token"
        return httpx.Response(200,json={"data":{"after":"t3_next","children":[{"data":{"name":"t3_1","title":"Night shift","selftext":"I was alone at the hospital when someone knocked.","permalink":"/r/Paranormal/comments/1/x/","author":"writer","created_utc":1700000000,"num_comments":9,"score":30,"subreddit":"Paranormal","subreddit_name_prefixed":"r/Paranormal","is_self":True}}]}})
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config=AppConfig(_env_file=None,reddit_client_id="id",reddit_client_secret="secret")
    try:items=await RedditSource(config,client).search("night shift",SearchOptions())
    finally:await client.aclose()
    assert calls==["/api/v1/access_token","/search"]
    assert items[0].source_url.startswith("https://www.reddit.com/")
    assert items[0].metadata["after"]=="t3_next"


@pytest.mark.asyncio
async def test_threads_retries_rate_limit(monkeypatch):
    attempts=0
    def handler(_request:httpx.Request):
        nonlocal attempts;attempts+=1
        if attempts==1:return httpx.Response(429,json={"error":{"message":"rate limited"}},headers={"retry-after":"0"})
        return httpx.Response(200,json={"data":[]})
    async def no_sleep(_seconds):return None
    monkeypatch.setattr("app.sources.http.asyncio.sleep",no_sleep)
    client=httpx.AsyncClient(transport=httpx.MockTransport(handler))
    config=AppConfig(_env_file=None,threads_access_token="secret",max_retries=1)
    try:await ThreadsSource(config,client).search("ghost",SearchOptions())
    finally:await client.aclose()
    assert attempts==2

