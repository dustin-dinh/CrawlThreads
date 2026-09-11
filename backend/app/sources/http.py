import asyncio
import logging
from collections.abc import Awaitable, Callable

import httpx

from app.core.config import get_config
from .base import SourceError

logger = logging.getLogger(__name__)


async def request_with_retry(
    operation: Callable[[], Awaitable[httpx.Response]],
    source: str,
    retries: int | None = None,
) -> httpx.Response:
    max_retries = retries if retries is not None else get_config().max_retries
    for attempt in range(max_retries + 1):
        try:
            response = await operation()
            if response.status_code == 429 or response.status_code >= 500:
                if attempt < max_retries:
                    retry_after = response.headers.get("retry-after")
                    delay = min(float(retry_after), 30.0) if retry_after and retry_after.isdigit() else min(2**attempt, 8)
                    logger.warning("rate_or_server_error source=%s status=%s retry=%s", source, response.status_code, attempt + 1)
                    await asyncio.sleep(delay)
                    continue
            response.raise_for_status()
            return response
        except (httpx.TimeoutException, httpx.NetworkError) as exc:
            if attempt >= max_retries:
                raise SourceError(f"{source}: không thể kết nối sau {max_retries + 1} lần thử") from exc
            await asyncio.sleep(min(2**attempt, 8))
        except httpx.HTTPStatusError as exc:
            detail = ""
            try:
                body = exc.response.json()
                detail = body.get("error", {}).get("message") or body.get("message") or ""
            except Exception:
                detail = exc.response.text[:250]
            raise SourceError(f"{source}: HTTP {exc.response.status_code} {detail}".strip()) from exc
    raise SourceError(f"{source}: lỗi không xác định")

