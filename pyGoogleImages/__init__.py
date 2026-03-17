"""pyGoogleImages — async Google Images search with proxy and safe-search.

Quick start::

    import anyio
    from pyGoogleImages import GoogleImageSearch, ImageResult

    async def main():
        async with GoogleImageSearch(safe_search=True) as search:
            results: list[ImageResult] = await search.search("sunset photos")
            for img in results:
                print(img.url, img.safe_search)      # attribute access
                print(img.to_dict()["safeSearch"])   # dict key (camelCase)

    anyio.run(main)
"""

from .models import ImageResult
from .searcher import GoogleImageSearch

__all__ = ["GoogleImageSearch", "ImageResult"]
