"""Async Google Images search client.

Example — basic search::

    import anyio
    from pyGoogleImages import GoogleImageSearch

    async def main():
        async with GoogleImageSearch(safe_search=True) as search:
            results = await search.search("cute cats", page=0)
            for img in results:
                print(img.url, img.safe_search)

    anyio.run(main)

Example — paginated generator::

    async def main():
        async with GoogleImageSearch() as search:
            async for img in search.search_all("sunsets", max_results=50):
                print(img.to_dict())

    anyio.run(main)

Example — with a proxy::

    async with GoogleImageSearch(proxy="http://user:pass@proxy:8080") as search:
        results = await search.search("mountains")
"""

from __future__ import annotations

import re
from collections.abc import AsyncIterator
from typing import Optional
from urllib.parse import urlencode

import httpx

from .models import ImageResult
from .parser import parse_images

# ── Constants ─────────────────────────────────────────────────────────────────

_SEARCH_URL = "https://www.google.com/search"

_DEFAULT_HEADERS: dict[str, str] = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/137.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": (
        "text/html,application/xhtml+xml,application/xml;"
        "q=0.9,image/webp,*/*;q=0.8"
    ),
    "Accept-Encoding": "gzip, deflate",
    "DNT": "1",
}

_DEFAULT_RESULTS_PER_PAGE = 20


# ── Public class ──────────────────────────────────────────────────────────────


class GoogleImageSearch:
    """Async Google Images search client with proxy and safe-search support.

    This class **must** be used as an async context manager so that the
    underlying :class:`httpx.AsyncClient` is properly initialised and closed::

        async with GoogleImageSearch(safe_search=True) as search:
            page_0 = await search.search("cats")

    Args:
        proxy:            Optional proxy URL forwarded to
                          :class:`httpx.AsyncClient`, e.g.
                          ``"http://user:pass@host:port"``.
        safe_search:      When ``True`` (default) Google's SafeSearch filter
                          is enabled and every returned :class:`ImageResult`
                          will have ``safe_search=True``.
        language:         BCP-47 language tag sent as the ``hl`` query
                          parameter (default ``"en"``).
        results_per_page: Maximum number of results to return per
                          :meth:`search` call (default 20).
        timeout:          HTTP request timeout in seconds (default 30).
    """

    def __init__(
        self,
        *,
        proxy: Optional[str] = None,
        safe_search: bool = True,
        language: str = "en",
        results_per_page: int = _DEFAULT_RESULTS_PER_PAGE,
        timeout: float = 30.0,
    ) -> None:
        self.proxy = proxy
        self.safe_search = safe_search
        self.language = language
        self.results_per_page = results_per_page
        self.timeout = timeout
        self._client: Optional[httpx.AsyncClient] = None

    # ── Context-manager protocol ──────────────────────────────────────────────

    async def __aenter__(self) -> "GoogleImageSearch":
        client_kwargs: dict = {
            "headers": _DEFAULT_HEADERS,
            "follow_redirects": True,
            "timeout": self.timeout,
        }
        if self.proxy:
            client_kwargs["proxy"] = self.proxy
        self._client = httpx.AsyncClient(**client_kwargs)
        return self

    async def __aexit__(
        self,
        exc_type: type | None,
        exc_val: BaseException | None,
        exc_tb: object,
    ) -> None:
        if self._client is not None:
            await self._client.aclose()
            self._client = None

    # ── Public search methods ─────────────────────────────────────────────────

    async def search(self, query: str, *, page: int = 0) -> list[ImageResult]:
        """Fetch one page of image results for *query*.

        Args:
            query: Search query string.
            page:  Zero-based page index. ``page=0`` is the first page,
                   ``page=1`` is the second, and so on.

        Returns:
            A list of up to ``results_per_page`` :class:`ImageResult` objects.
            Every result carries a ``safe_search`` attribute that reflects the
            setting used when the search was performed.

        Raises:
            RuntimeError:             When called outside an ``async with``
                                      block.
            httpx.HTTPStatusError:    On a non-2xx response from Google.
            httpx.RequestError:       On network-level failures.
        """
        client = self._require_client()
        url = self._build_url(query, page)
        response = await client.get(url)
        response.raise_for_status()

        raw = parse_images(response.text)
        if not raw and self._looks_like_google_js_gate(response.text):
            raise RuntimeError(
                "Google returned a JS/anti-bot page instead of image results. "
                "Try a residential proxy, lower request rate, or a different IP."
            )
        return [
            ImageResult(
                url=item["url"],
                title=item["title"],
                source_url=item["source_url"],
                source_domain=item["source_domain"],
                thumbnail_url=item["thumbnail_url"],
                width=item["width"],
                height=item["height"],
                safe_search=self.safe_search,
            )
            for item in raw[: self.results_per_page]
        ]

    async def search_all(
        self,
        query: str,
        *,
        max_results: int = 100,
    ) -> AsyncIterator[ImageResult]:
        """Async generator that yields images across multiple pages.

        Automatically advances through pages until *max_results* images have
        been yielded or Google returns an empty page.

        Args:
            query:       Search query string.
            max_results: Maximum total number of images to yield (default 100).

        Yields:
            :class:`ImageResult` objects, each tagged with ``safe_search``.

        Raises:
            RuntimeError:          When called outside an ``async with`` block.
            httpx.HTTPStatusError: On a non-2xx response from Google.
            httpx.RequestError:    On network-level failures.

        Example::

            async with GoogleImageSearch() as s:
                async for img in s.search_all("puppies", max_results=50):
                    print(img.url)
        """
        page = 0
        yielded = 0

        while yielded < max_results:
            results = await self.search(query, page=page)
            if not results:
                return
            for result in results:
                if yielded >= max_results:
                    return
                yield result
                yielded += 1
            page += 1

    # ── Private helpers ───────────────────────────────────────────────────────

    def _build_url(self, query: str, page: int) -> str:
        """Construct the Google Images search URL."""
        params = {
            "q": query,
            "tbm": "isch",
            "safe": "active" if self.safe_search else "off",
            "ijn": str(page),
            "start": str(page * self.results_per_page),
            "hl": self.language,
        }
        return f"{_SEARCH_URL}?{urlencode(params)}"

    def _require_client(self) -> httpx.AsyncClient:
        """Return the active client or raise a helpful error."""
        if self._client is None:
            raise RuntimeError(
                "GoogleImageSearch must be used as an async context manager.\n"
                "Use:  async with GoogleImageSearch() as search: ..."
            )
        return self._client

    @staticmethod
    def _looks_like_google_js_gate(html: str) -> bool:
        """Detect Google's JS/anti-bot pages that contain no image payload."""
        lowered = html.lower()
        markers = (
            "enablejs",
            "our systems have detected unusual traffic",
            "sorry/index",
            "g-recaptcha",
            "captcha",
        )
        return any(marker in lowered for marker in markers)
