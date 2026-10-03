import pytest

from conftest import BASE
from webcollect.collector import collect
from webcollect.fetcher import Fetcher, FetchError


class Resp:
    def __init__(self, status, text=""):
        self.status_code, self.text, self.encoding = status, text, "utf-8"

    def raise_for_status(self):
        if self.status_code >= 400:
            import requests
            raise requests.HTTPError(str(self.status_code))


def make_fetcher(monkeypatch, robots_status, robots_text="", page="<html></html>"):
    slept = []
    f = Fetcher("test-agent", delay_seconds=1.0, timeout_seconds=5, max_retries=0, sleep=slept.append)
    def fake_get(url, timeout):
        return Resp(robots_status, robots_text) if url.endswith("robots.txt") else Resp(200, page)
    monkeypatch.setattr(f.session, "get", fake_get)
    return f, slept


def test_robots_disallow_stops(monkeypatch):
    f, _ = make_fetcher(monkeypatch, 200, "User-agent: *\nDisallow: /private/\n")
    assert f.get("https://example.com/public/a") == "<html></html>"
    with pytest.raises(FetchError, match="robots.txt"):
        f.get("https://example.com/private/a")


def test_robots_missing_means_allowed(monkeypatch):
    f, _ = make_fetcher(monkeypatch, 404)
    f.get("https://example.com/anything")
    assert f.count == 1


def test_robots_forbidden_means_disallowed(monkeypatch):
    f, _ = make_fetcher(monkeypatch, 403)
    with pytest.raises(FetchError):
        f.get("https://example.com/anything")


def test_waits_between_requests(monkeypatch):
    f, slept = make_fetcher(monkeypatch, 404)
    for _ in range(3):
        f.get("https://example.com/x")
    # robots.txt を含めて4回のリクエスト。2回目以降は前回から1秒あける
    assert len(slept) == 3 and all(0.9 < s <= 1.0 for s in slept)


def test_collect_one_category(fake_fetcher):
    books = collect(fake_fetcher, BASE, ["Mystery"], fetch_details=False)
    assert len(books) == 32
    assert fake_fetcher.count == 3  # トップ＋2ページ
    assert all(b.category == "Mystery" for b in books)


def test_collect_with_details(fake_fetcher):
    books = collect(fake_fetcher, BASE, ["Mystery"], fetch_details=True)
    assert all(b.stock_count == 20 and b.upc for b in books)
    assert fake_fetcher.count == 3 + 32


def test_collect_unknown_category(fake_fetcher):
    with pytest.raises(ValueError, match="サイトにない"):
        collect(fake_fetcher, BASE, ["存在しないカテゴリ"], fetch_details=False)
