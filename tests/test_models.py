# tests/test_models.py
"""Tests for the ImageResult dataclass."""
from __future__ import annotations

import pytest
from pyGoogleImages.models import ImageResult


def _make_result(**kwargs) -> ImageResult:
    defaults = {
        "url": "https://example.com/img.jpg",
        "title": "Sample image",
        "source_url": "https://example.com/page",
        "source_domain": "example.com",
        "thumbnail_url": "https://thumb.example.com/t.jpg",
        "width": 800,
        "height": 600,
        "safe_search": True,
    }
    defaults.update(kwargs)
    return ImageResult(**defaults)


class TestImageResult:
    def test_fields_stored(self):
        img = _make_result()
        assert img.url == "https://example.com/img.jpg"
        assert img.title == "Sample image"
        assert img.source_url == "https://example.com/page"
        assert img.source_domain == "example.com"
        assert img.thumbnail_url == "https://thumb.example.com/t.jpg"
        assert img.width == 800
        assert img.height == 600
        assert img.safe_search is True

    def test_safe_search_false(self):
        img = _make_result(safe_search=False)
        assert img.safe_search is False

    def test_to_dict_safe_search_true(self):
        d = _make_result(safe_search=True).to_dict()
        assert d["safeSearch"] is True
        assert d["url"] == "https://example.com/img.jpg"
        assert d["title"] == "Sample image"
        assert d["source_url"] == "https://example.com/page"
        assert d["source_domain"] == "example.com"
        assert d["thumbnail_url"] == "https://thumb.example.com/t.jpg"
        assert d["width"] == 800
        assert d["height"] == 600

    def test_to_dict_safe_search_false(self):
        d = _make_result(safe_search=False).to_dict()
        assert d["safeSearch"] is False

    def test_to_dict_keys(self):
        """to_dict must contain exactly the documented keys."""
        expected_keys = {
            "url",
            "title",
            "source_url",
            "source_domain",
            "thumbnail_url",
            "width",
            "height",
            "safeSearch",
        }
        assert set(_make_result().to_dict().keys()) == expected_keys

    def test_zero_dimensions_allowed(self):
        img = _make_result(width=0, height=0)
        assert img.width == 0
        assert img.height == 0
        assert img.to_dict()["width"] == 0
