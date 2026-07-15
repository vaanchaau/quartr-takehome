"""Async HTTP client with retrying GETs against full URLs."""

from __future__ import annotations

import asyncio
import random
import sys

import httpx

DEFAULT_TIMEOUT_SECONDS = 10.0
DEFAULT_MAX_RETRIES = 3
DEFAULT_BACKOFF_BASE_SECONDS = 1.0


class HttpClient:
    """Wraps an httpx.AsyncClient, with headers set on every request."""

    def __init__(
        self,
        headers: dict[str, str],
        *,
        timeout_seconds: float = DEFAULT_TIMEOUT_SECONDS,
        max_retries: int = DEFAULT_MAX_RETRIES,
        backoff_base_seconds: float = DEFAULT_BACKOFF_BASE_SECONDS,
    ) -> None:
        self._client = httpx.AsyncClient(headers=headers, timeout=timeout_seconds)
        self._max_retries = max_retries
        self._backoff_base_seconds = backoff_base_seconds

    async def __aenter__(self) -> HttpClient:
        await self._client.__aenter__()
        return self

    async def __aexit__(self, *exc_info: object) -> None:
        await self._client.__aexit__(*exc_info)

    async def try_get(self, url: str) -> httpx.Response | None:
        """GET url. Logs and returns None on request errors (transport, decoding,
        too-many-redirects); logs and returns the response as-is on error statuses."""
        try:
            response = await self._client.get(url)
        except httpx.RequestError as exc:
            print(f"{type(exc).__name__} fetching {url}: {exc}", file=sys.stderr)
            return None

        if response.is_error:
            print(f"HTTP {response.status_code} fetching {url}", file=sys.stderr)
        return response

    async def try_get_with_retry(self, url: str) -> httpx.Response:
        """GET url, retrying on 429/5xx/transport errors up to max_retries."""
        for attempt in range(self._max_retries + 1):
            response = await self.try_get(url)
            is_last_attempt = attempt == self._max_retries

            if response is not None and not _is_retryable(response):
                response.raise_for_status()
                return response

            if is_last_attempt:
                if response is not None:
                    response.raise_for_status()
                raise httpx.TransportError(f"exhausted retries fetching {url}")

            await asyncio.sleep(_delay_seconds(attempt, self._backoff_base_seconds, response))

        raise AssertionError("unreachable")


def _is_retryable(response: httpx.Response) -> bool:
    return response.status_code == 429 or response.status_code >= 500


def _delay_seconds(
    attempt: int, backoff_base_seconds: float, response: httpx.Response | None
) -> float:
    retry_after = response.headers.get("Retry-After") if response is not None else None
    if retry_after is not None:
        try:
            return float(retry_after)
        except ValueError:
            pass  # Retry-After can also be an HTTP-date; fall back to backoff.
    return backoff_base_seconds * (2**attempt) + random.uniform(0, backoff_base_seconds)
