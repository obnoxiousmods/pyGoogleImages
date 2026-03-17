# tests/test_searcher.py
"""Tests for the GoogleImageSearch async client."""
from __future__ import annotations

import pytest
import respx
import httpx

from pyGoogleImages import GoogleImageSearch, ImageResult


# ── Shared HTML fixture (reuse conftest html_single) ─────────────────────────


@pytest.fixture
def google_url():
    return "https://www.google.com/search"


# ── Helpers ───────────────────────────────────────────────────────────────────

def _make_html_with_images(n: int, domain: str = "example.com") -> str:
    """Build a minimal Google Images HTML snippet with *n* image results."""
    blocks = []
    for i in range(1, n + 1):
        blocks.append(
            f"""var img{i} = {{
  "ou":"https://{domain}/image{i}.jpg",
  "ow":{800 + i * 10},
  "oh":{600 + i * 10},
  "pt":"Image {i}",
  "rh":"{domain}",
  "ru":"https://{domain}/page{i}",
  "tu":"https://encrypted-tbn0.gstatic.com/t{i}",
  "tw":150,
  "th":112
}};"""
        )
    return "<html><body><script>" + "\n".join(blocks) + "</script></body></html>"


# ── Context-manager lifecycle ─────────────────────────────────────────────────


class TestContextManager:
    @pytest.mark.anyio
    async def test_enter_creates_client(self):
        async with GoogleImageSearch() as s:
            assert s._client is not None

    @pytest.mark.anyio
    async def test_exit_closes_client(self):
        s = GoogleImageSearch()
        async with s:
            pass
        assert s._client is None

    @pytest.mark.anyio
    async def test_requires_context_manager(self):
        s = GoogleImageSearch()
        with pytest.raises(RuntimeError, match="async context manager"):
            await s.search("cats")


# ── URL construction ──────────────────────────────────────────────────────────


class TestBuildUrl:
    def test_safe_search_active(self):
        s = GoogleImageSearch(safe_search=True)
        url = s._build_url("cats", 0)
        assert "safe=active" in url

    def test_safe_search_off(self):
        s = GoogleImageSearch(safe_search=False)
        url = s._build_url("cats", 0)
        assert "safe=off" in url

    def test_query_encoded(self):
        s = GoogleImageSearch()
        url = s._build_url("cute cats & dogs", 0)
        assert "cute+cats" in url or "cute%20cats" in url

    def test_page_zero(self):
        s = GoogleImageSearch()
        url = s._build_url("cats", 0)
        assert "ijn=0" in url
        assert "start=0" in url

    def test_page_one(self):
        s = GoogleImageSearch(results_per_page=20)
        url = s._build_url("cats", 1)
        assert "ijn=1" in url
        assert "start=20" in url

    def test_page_two(self):
        s = GoogleImageSearch(results_per_page=10)
        url = s._build_url("cats", 2)
        assert "start=20" in url

    def test_language_param(self):
        s = GoogleImageSearch(language="de")
        url = s._build_url("Katzen", 0)
        assert "hl=de" in url

    def test_tbm_param(self):
        s = GoogleImageSearch()
        url = s._build_url("cats", 0)
        assert "tbm=isch" in url


# ── search() ─────────────────────────────────────────────────────────────────


class TestSearch:
    @pytest.mark.anyio
    async def test_returns_image_results(self, html_single):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_single)
            )
            async with GoogleImageSearch(safe_search=True) as s:
                results = await s.search("cats")

        assert len(results) == 1
        assert isinstance(results[0], ImageResult)

    @pytest.mark.anyio
    async def test_result_fields_populated(self, html_single):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_single)
            )
            async with GoogleImageSearch() as s:
                results = await s.search("cats")

        img = results[0]
        assert img.url == "https://example.com/images/cat.jpg"
        assert img.title == "A cute tabby cat"
        assert img.source_domain == "example.com"
        assert img.width == 800
        assert img.height == 600

    @pytest.mark.anyio
    async def test_safe_search_true_propagated(self, html_single):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_single)
            )
            async with GoogleImageSearch(safe_search=True) as s:
                results = await s.search("cats")

        assert all(r.safe_search is True for r in results)

    @pytest.mark.anyio
    async def test_safe_search_false_propagated(self, html_single):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_single)
            )
            async with GoogleImageSearch(safe_search=False) as s:
                results = await s.search("cats")

        assert all(r.safe_search is False for r in results)

    @pytest.mark.anyio
    async def test_to_dict_has_safe_search_key(self, html_single):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_single)
            )
            async with GoogleImageSearch(safe_search=True) as s:
                results = await s.search("cats")

        d = results[0].to_dict()
        assert "safeSearch" in d
        assert d["safeSearch"] is True

    @pytest.mark.anyio
    async def test_respects_results_per_page_limit(self):
        """Even if the page has 5 images, only 3 should be returned."""
        html = _make_html_with_images(5)
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html)
            )
            async with GoogleImageSearch(results_per_page=3) as s:
                results = await s.search("dogs")

        assert len(results) == 3

    @pytest.mark.anyio
    async def test_http_error_propagates(self):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(429)
            )
            async with GoogleImageSearch() as s:
                with pytest.raises(httpx.HTTPStatusError):
                    await s.search("cats")

    @pytest.mark.anyio
    async def test_empty_page_returns_empty_list(self, html_empty):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_empty)
            )
            async with GoogleImageSearch() as s:
                results = await s.search("xyzzy")

        assert results == []

    @pytest.mark.anyio
    async def test_js_gate_page_raises_runtime_error(self):
        html = "<html><body>enablejs captcha</body></html>"
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html)
            )
            async with GoogleImageSearch() as s:
                with pytest.raises(RuntimeError, match="JS/anti-bot"):
                    await s.search("cats")

    @pytest.mark.anyio
    async def test_page_param_reflected_in_url(self):
        captured_requests = []

        async def capture(request):
            captured_requests.append(request)
            return httpx.Response(200, text="<html></html>")

        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                side_effect=capture
            )
            async with GoogleImageSearch(results_per_page=20) as s:
                await s.search("cats", page=3)

        url = str(captured_requests[0].url)
        assert "ijn=3" in url
        assert "start=60" in url


# ── search_all() ──────────────────────────────────────────────────────────────


class TestSearchAll:
    @pytest.mark.anyio
    async def test_yields_results_across_pages(self):
        """Two calls to the mock return a page with 2 images each."""
        pages = [_make_html_with_images(2, "page1.com"), _make_html_with_images(2, "page2.com")]
        call_count = 0

        async def handler(request):
            nonlocal call_count
            html = pages[min(call_count, len(pages) - 1)]
            call_count += 1
            return httpx.Response(200, text=html)

        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                side_effect=handler
            )
            async with GoogleImageSearch() as s:
                results = []
                async for img in s.search_all("cats", max_results=4):
                    results.append(img)

        assert len(results) == 4
        assert all(isinstance(r, ImageResult) for r in results)

    @pytest.mark.anyio
    async def test_max_results_respected(self):
        html = _make_html_with_images(10)
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html)
            )
            async with GoogleImageSearch(results_per_page=10) as s:
                results = []
                async for img in s.search_all("cats", max_results=5):
                    results.append(img)

        assert len(results) == 5

    @pytest.mark.anyio
    async def test_stops_on_empty_page(self):
        """After the first page returns no results, the generator stops."""
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text="<html></html>")
            )
            async with GoogleImageSearch() as s:
                results = []
                async for img in s.search_all("cats", max_results=100):
                    results.append(img)

        assert results == []

    @pytest.mark.anyio
    async def test_safe_search_propagated_in_generator(self, html_single):
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text=html_single)
            )
            async with GoogleImageSearch(safe_search=False) as s:
                results = []
                async for img in s.search_all("cats", max_results=10):
                    results.append(img)

        assert all(r.safe_search is False for r in results)


# ── Proxy configuration ───────────────────────────────────────────────────────


class TestProxyConfiguration:
    def test_proxy_stored(self):
        s = GoogleImageSearch(proxy="http://proxy:8080")
        assert s.proxy == "http://proxy:8080"

    def test_no_proxy_by_default(self):
        s = GoogleImageSearch()
        assert s.proxy is None

    @pytest.mark.anyio
    async def test_proxy_passed_to_client(self):
        """Verify that when a proxy is set, the AsyncClient is initialised."""
        with respx.mock:
            respx.get(url__startswith="https://www.google.com/search").mock(
                return_value=httpx.Response(200, text="<html></html>")
            )
            async with GoogleImageSearch(proxy="http://proxy:8080") as s:
                assert s._client is not None
                await s.search("test")
