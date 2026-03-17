"""HTML parsing utilities for Google Images search results.

Google Images embeds image metadata as JSON fragments inside ``<script>``
blocks.  The keys used by Google are:

* ``ou``  – original image URL
* ``pt``  – title / alt-text
* ``ru``  – URL of the result page that hosts the image
* ``rh``  – referring host (domain)
* ``ow``  – original image width (pixels)
* ``oh``  – original image height (pixels)
* ``tu``  – thumbnail URL

The parser tries two strategies in order:

1. **Script-JSON strategy** – find every ``"ou":"https://..."`` occurrence in
   the raw HTML and correlate nearby sibling keys using a sliding window.
2. **Fallback img-src strategy** – if strategy 1 returns nothing, scrape
   ``<img src="...">`` tags (usually returns only thumbnails).
"""

from __future__ import annotations

import html as _html
import re

# ── Google metadata keys ────────────────────────────────────────────────────
_K_URL = "ou"
_K_TITLE = "pt"
_K_SOURCE_URL = "ru"
_K_DOMAIN = "rh"
_K_WIDTH = "ow"
_K_HEIGHT = "oh"
_K_THUMB = "tu"

# Minimum reasonable image dimension to skip Google UI assets
_MIN_DIM = 50

# How many characters to scan on each side of an "ou" match for sibling keys
_WINDOW = 800


def parse_images(html: str) -> list[dict]:
    """Return a list of image-metadata dicts parsed from a Google Images page.

    Each dict contains the keys: ``url``, ``title``, ``source_url``,
    ``source_domain``, ``thumbnail_url``, ``width``, ``height``.
    """
    results = _strategy_script_json(html)
    if not results:
        results = _strategy_img_src(html)
    return results


# ── Strategy 1 ───────────────────────────────────────────────────────────────


def _strategy_script_json(html: str) -> list[dict]:
    """Extract image data from embedded Google JSON fragments."""
    results: list[dict] = []
    seen: set[str] = set()

    # Google often escapes URLs in JSON as "https:\/\/...".
    for ou_m in re.finditer(r'"ou"\s*:\s*"((?:\\.|[^"\\])+)"', html):
        raw_url = ou_m.group(1)
        url = _clean_url(raw_url)
        if not (url.startswith("http://") or url.startswith("https://")):
            continue
        if not url or url in seen:
            continue

        # Collect a text window around the match to find sibling keys
        win_start = max(0, ou_m.start() - _WINDOW)
        win_end = min(len(html), ou_m.end() + _WINDOW)
        ctx = html[win_start:win_end]

        # Compute the position of the "ou" key within the context window so
        # that _str_field / _int_field can pick the nearest match when the
        # window contains data from multiple adjacent image objects.
        anchor = ou_m.start() - win_start

        title = _html.unescape(_str_field(ctx, _K_TITLE, anchor))
        source_url = _clean_url(_str_field(ctx, _K_SOURCE_URL, anchor))
        domain = _str_field(ctx, _K_DOMAIN, anchor)
        thumb = _clean_url(_str_field(ctx, _K_THUMB, anchor))
        width = _int_field(ctx, _K_WIDTH, anchor)
        height = _int_field(ctx, _K_HEIGHT, anchor)

        seen.add(url)
        results.append(
            {
                "url": url,
                "title": title,
                "source_url": source_url,
                "source_domain": domain,
                "thumbnail_url": thumb,
                "width": width,
                "height": height,
            }
        )

    return results


# ── Strategy 2 ───────────────────────────────────────────────────────────────


def _strategy_img_src(html: str) -> list[dict]:
    """Fallback: extract image URLs from ``<img src="...">`` attributes."""
    results: list[dict] = []
    seen: set[str] = set()

    for m in re.finditer(r'<img[^>]+\bsrc="(https?://[^"]+)"', html):
        url = m.group(1)
        if url in seen:
            continue
        seen.add(url)
        results.append(
            {
                "url": url,
                "title": "",
                "source_url": "",
                "source_domain": "",
                "thumbnail_url": url,
                "width": 0,
                "height": 0,
            }
        )

    return results


# ── Helpers ───────────────────────────────────────────────────────────────────


def _str_field(ctx: str, key: str, anchor: int = 0) -> str:
    """Return the string value of *key* **nearest** to *anchor* in *ctx*.

    When a context window contains data from multiple adjacent image objects
    the nearest match to the originating ``ou`` position is selected, avoiding
    cross-contamination between adjacent results.
    """
    pattern = re.compile(rf'"{re.escape(key)}"\s*:\s*"([^"]*)"')
    best: re.Match | None = None
    best_dist = float("inf")
    for m in pattern.finditer(ctx):
        dist = abs(m.start() - anchor)
        if dist < best_dist:
            best_dist = dist
            best = m
    return best.group(1) if best else ""


def _int_field(ctx: str, key: str, anchor: int = 0) -> int:
    """Return the integer value of *key* **nearest** to *anchor* in *ctx*, or ``0``."""
    pattern = re.compile(rf'"{re.escape(key)}"\s*:\s*(\d+)')
    best: re.Match | None = None
    best_dist = float("inf")
    for m in pattern.finditer(ctx):
        dist = abs(m.start() - anchor)
        if dist < best_dist:
            best_dist = dist
            best = m
    return int(best.group(1)) if best else 0


def _clean_url(url: str) -> str:
    """Normalise a URL extracted from JavaScript / JSON source.

    Replaces common JSON-escaped characters and collapses escaped slashes.
    """
    if not url:
        return url
    url = url.replace("\\u003d", "=")
    url = url.replace("\\u0026", "&")
    url = url.replace("\\/", "/")
    return url
