from pathlib import Path

import pytest

FIX = Path(__file__).parent / "fixtures"
BASE = "https://books.toscrape.com/"
PAGES = {
    BASE + "index.html": "home.html",
    BASE + "catalogue/category/books/mystery_3/index.html": "mystery_p1.html",
    BASE + "catalogue/category/books/mystery_3/page-2.html": "mystery_p2.html",
    BASE + "catalogue/sharp-objects_997/index.html": "detail_sharp_objects.html",
}


def fixture_html(name: str) -> str:
    return (FIX / name).read_text(encoding="utf-8")


class FakeFetcher:
    """ネットにつながず、保存したページを返す。"""

    def __init__(self, pages=None):
        self.pages = pages or PAGES
        self.count = 0
        self.urls = []

    def get(self, url):
        self.urls.append(url)
        self.count += 1
        if url in self.pages:
            return fixture_html(self.pages[url])
        if "/catalogue/" in url and url.endswith("/index.html") and "/category/" not in url:
            return fixture_html("detail_sharp_objects.html")  # 詳細ページはどれも同じ形
        raise AssertionError(f"想定外の URL: {url}")


@pytest.fixture
def fake_fetcher():
    return FakeFetcher()
