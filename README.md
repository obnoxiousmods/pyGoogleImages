# pyGoogleImages

An async Python library for searching Google Images — with **proxy support**, **safe-search control**, and **pagination** — built on top of [HTTPX](https://www.python-httpx.org/) and [anyio](https://anyio.readthedocs.io/).

---

## Features

| Feature | Details |
|---|---|
| **Async-first** | Built on `httpx.AsyncClient`; fully compatible with asyncio and trio via anyio |
| **Proxy support** | Pass any HTTP/SOCKS proxy URL directly to the client |
| **Safe-search** | Toggle `safe_search=True/False`; every result is tagged with `safeSearch` |
| **Pagination** | `search(page=N)` for one-shot pages; `search_all()` async generator for multi-page iteration |
| **Rich results** | Each `ImageResult` contains URL, title, source URL, domain, thumbnail URL, and dimensions |

---

## Installation

```bash
pip install pyGoogleImages
```

**Runtime dependencies** (installed automatically):

* `httpx >= 0.27`
* `anyio >= 4.0`
* `beautifulsoup4 >= 4.12`
* `lxml >= 5.0`

---

## Quick start

### Single page of results

```python
import anyio
from pyGoogleImages import GoogleImageSearch

async def main():
    async with GoogleImageSearch(safe_search=True) as search:
        results = await search.search("cute cats")
        for img in results:
            print(img.url)
            print(img.to_dict())   # includes "safeSearch": True

anyio.run(main)
```

### Paginated generator — iterate across many pages

```python
import anyio
from pyGoogleImages import GoogleImageSearch

async def main():
    async with GoogleImageSearch(safe_search=False) as search:
        async for img in search.search_all("mountain landscapes", max_results=60):
            print(img.url, "safeSearch:", img.safe_search)

anyio.run(main)
```

### With a proxy

```python
import anyio
from pyGoogleImages import GoogleImageSearch

async def main():
    async with GoogleImageSearch(
        proxy="http://user:password@proxy.example.com:8080",
        safe_search=True,
    ) as search:
        results = await search.search("sunsets", page=0)
        for img in results:
            print(img.to_dict())

anyio.run(main)
```

---

## API reference

### `GoogleImageSearch`

```python
GoogleImageSearch(
    *,
    proxy: str | None = None,
    safe_search: bool = True,
    language: str = "en",
    results_per_page: int = 20,
    timeout: float = 30.0,
)
```

| Parameter | Type | Default | Description |
|---|---|---|---|
| `proxy` | `str \| None` | `None` | Optional proxy URL, e.g. `"http://host:port"` |
| `safe_search` | `bool` | `True` | Enable/disable Google SafeSearch |
| `language` | `str` | `"en"` | BCP-47 language tag for the `hl` query parameter |
| `results_per_page` | `int` | `20` | Max results per `search()` call |
| `timeout` | `float` | `30.0` | HTTP timeout in seconds |

**Must be used as an async context manager.**

#### `await search.search(query, *, page=0) → list[ImageResult]`

Fetch one page of results. `page=0` is the first page, `page=1` the second, etc.

#### `search.search_all(query, *, max_results=100) → AsyncIterator[ImageResult]`

Async generator that automatically advances pages until `max_results` images
have been yielded or Google returns an empty page.

---

### `ImageResult`

```python
@dataclass
class ImageResult:
    url:           str   # direct URL to the full-size image
    title:         str   # alt text / image title
    source_url:    str   # URL of the page that hosts the image
    source_domain: str   # hostname of the source page
    thumbnail_url: str   # Google-hosted thumbnail URL
    width:         int   # original width in pixels (0 if unknown)
    height:        int   # original height in pixels (0 if unknown)
    safe_search:   bool  # True if SafeSearch was active for this search
```

#### `.to_dict() → dict`

Serialises the result to a plain dict.  The `safe_search` field is exported
under the camelCase key `"safeSearch"`:

```python
{
    "url": "https://example.com/cat.jpg",
    "title": "A cute tabby cat",
    "source_url": "https://example.com/cat-article",
    "source_domain": "example.com",
    "thumbnail_url": "https://encrypted-tbn0.gstatic.com/...",
    "width": 800,
    "height": 600,
    "safeSearch": True
}
```

---

## Running the tests

```bash
pip install -e ".[dev]"
pytest
```

---

## License

MIT

