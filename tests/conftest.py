# tests/conftest.py
"""Shared pytest fixtures for pyGoogleImages tests."""
from __future__ import annotations

import pytest


# ---------------------------------------------------------------------------
# Minimal Google Images HTML fixtures
# ---------------------------------------------------------------------------
# These fixtures reproduce the relevant portions of a real Google Images
# search-result page: the "ou" / "pt" / "ru" / "rh" / "ow" / "oh" / "tu"
# JSON keys embedded inside <script> blocks.
# ---------------------------------------------------------------------------

_FIXTURE_SINGLE = """
<html><body>
<script>
AF_initDataCallback({key:'ds:1', data:function(){return [null,[
  [null,null,null,
    ["https://example.com/images/cat.jpg",800,600],
    ["https://encrypted-tbn0.gstatic.com/thumb?q=cat",150,112]
  ]
]];}});
</script>
<script>
var _data = {
  "ou":"https://example.com/images/cat.jpg",
  "ow":800,
  "oh":600,
  "pt":"A cute tabby cat",
  "rh":"example.com",
  "ru":"https://example.com/cat-article",
  "tu":"https://encrypted-tbn0.gstatic.com/thumb?q=cat",
  "tw":150,
  "th":112
};
</script>
</body></html>
"""

_FIXTURE_MULTIPLE = """
<html><body>
<script>
var img1 = {
  "ou":"https://site1.com/photos/dog.jpg",
  "ow":1024,
  "oh":768,
  "pt":"Golden retriever",
  "rh":"site1.com",
  "ru":"https://site1.com/dogs",
  "tu":"https://encrypted-tbn0.gstatic.com/t1",
  "tw":200,
  "th":150
};
var img2 = {
  "ou":"https://site2.org/pics/pug.png",
  "ow":640,
  "oh":480,
  "pt":"Cute pug dog",
  "rh":"site2.org",
  "ru":"https://site2.org/pugs",
  "tu":"https://encrypted-tbn0.gstatic.com/t2",
  "tw":180,
  "th":135
};
</script>
</body></html>
"""

_FIXTURE_NO_OU = """
<html><body>
<script>var nothing = "hello world";</script>
<img src="https://fallback.example.com/image.jpg" alt="fallback image">
</body></html>
"""

_FIXTURE_EMPTY = "<html><body><p>No results.</p></body></html>"


@pytest.fixture
def html_single() -> str:
    """HTML with a single image result (strategy-1 parseable)."""
    return _FIXTURE_SINGLE


@pytest.fixture
def html_multiple() -> str:
    """HTML with two image results (strategy-1 parseable)."""
    return _FIXTURE_MULTIPLE


@pytest.fixture
def html_no_ou() -> str:
    """HTML without 'ou' keys — triggers fallback strategy."""
    return _FIXTURE_NO_OU


@pytest.fixture
def html_empty() -> str:
    """HTML with no image data at all."""
    return _FIXTURE_EMPTY
