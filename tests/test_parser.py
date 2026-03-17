# tests/test_parser.py
"""Tests for the HTML parsing utilities."""
from __future__ import annotations

import pytest
from pyGoogleImages.parser import parse_images, _clean_url


class TestParseImagesSingleResult:
    def test_returns_list(self, html_single):
        results = parse_images(html_single)
        assert isinstance(results, list)

    def test_one_result(self, html_single):
        results = parse_images(html_single)
        assert len(results) == 1

    def test_url_extracted(self, html_single):
        result = parse_images(html_single)[0]
        assert result["url"] == "https://example.com/images/cat.jpg"

    def test_title_extracted(self, html_single):
        result = parse_images(html_single)[0]
        assert result["title"] == "A cute tabby cat"

    def test_source_url_extracted(self, html_single):
        result = parse_images(html_single)[0]
        assert result["source_url"] == "https://example.com/cat-article"

    def test_source_domain_extracted(self, html_single):
        result = parse_images(html_single)[0]
        assert result["source_domain"] == "example.com"

    def test_thumbnail_url_extracted(self, html_single):
        result = parse_images(html_single)[0]
        assert result["thumbnail_url"] == "https://encrypted-tbn0.gstatic.com/thumb?q=cat"

    def test_dimensions_extracted(self, html_single):
        result = parse_images(html_single)[0]
        assert result["width"] == 800
        assert result["height"] == 600


class TestParseImagesMultipleResults:
    def test_two_results_returned(self, html_multiple):
        results = parse_images(html_multiple)
        assert len(results) == 2

    def test_first_result_url(self, html_multiple):
        results = parse_images(html_multiple)
        assert results[0]["url"] == "https://site1.com/photos/dog.jpg"

    def test_second_result_url(self, html_multiple):
        results = parse_images(html_multiple)
        assert results[1]["url"] == "https://site2.org/pics/pug.png"

    def test_second_result_title(self, html_multiple):
        results = parse_images(html_multiple)
        assert results[1]["title"] == "Cute pug dog"

    def test_no_duplicates(self, html_multiple):
        results = parse_images(html_multiple)
        urls = [r["url"] for r in results]
        assert len(urls) == len(set(urls))


class TestParseImagesFallback:
    def test_fallback_triggered_when_no_ou(self, html_no_ou):
        results = parse_images(html_no_ou)
        assert len(results) == 1
        assert results[0]["url"] == "https://fallback.example.com/image.jpg"

    def test_fallback_thumbnail_equals_url(self, html_no_ou):
        result = parse_images(html_no_ou)[0]
        assert result["thumbnail_url"] == result["url"]

    def test_fallback_empty_metadata(self, html_no_ou):
        result = parse_images(html_no_ou)[0]
        assert result["title"] == ""
        assert result["source_url"] == ""
        assert result["width"] == 0
        assert result["height"] == 0


class TestParseImagesEmpty:
    def test_empty_html_returns_empty_list(self, html_empty):
        assert parse_images(html_empty) == []


class TestCleanUrl:
    def test_passthrough_normal_url(self):
        url = "https://example.com/image.jpg"
        assert _clean_url(url) == url

    def test_replaces_escaped_equals(self):
        assert _clean_url("https://x.com/img?a\\u003db") == "https://x.com/img?a=b"

    def test_replaces_escaped_ampersand(self):
        assert _clean_url("https://x.com/img?a=1\\u0026b=2") == "https://x.com/img?a=1&b=2"

    def test_replaces_escaped_slash(self):
        assert _clean_url("https:\\/\\/x.com") == "https://x.com"

    def test_empty_string_passthrough(self):
        assert _clean_url("") == ""
