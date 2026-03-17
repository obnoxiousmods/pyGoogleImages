"""Data models for pyGoogleImages."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass
class ImageResult:
    """A single image result returned from a Google Images search.

    Attributes:
        url:           Direct URL to the full-size image.
        title:         Alt text / title of the image.
        source_url:    URL of the page on which the image was found.
        source_domain: Hostname of the source page (e.g. ``"example.com"``).
        thumbnail_url: URL of the Google-hosted thumbnail for the image.
        width:         Original image width in pixels (0 if unknown).
        height:        Original image height in pixels (0 if unknown).
        safe_search:   ``True`` when the search was performed with SafeSearch
                       enabled; ``False`` otherwise.
    """

    url: str
    title: str
    source_url: str
    source_domain: str
    thumbnail_url: str
    width: int
    height: int
    safe_search: bool

    def to_dict(self) -> dict:
        """Serialise the result to a plain dictionary.

        The ``safe_search`` field is exported under the camelCase key
        ``"safeSearch"`` to match the documented API contract.
        """
        return {
            "url": self.url,
            "title": self.title,
            "source_url": self.source_url,
            "source_domain": self.source_domain,
            "thumbnail_url": self.thumbnail_url,
            "width": self.width,
            "height": self.height,
            "safeSearch": self.safe_search,
        }
