from decimal import Decimal

import pytest

from conftest import BASE, fixture_html
from webcollect.parser import ParseError, parse_categories, parse_detail, parse_list_page

P1 = BASE + "catalogue/category/books/mystery_3/index.html"


def test_categories():
    cats = parse_categories(fixture_html("home.html"), BASE + "index.html")
    assert len(cats) == 50
    assert cats["Mystery"] == P1


def test_list_page_first_and_next():
    books, nxt = parse_list_page(fixture_html("mystery_p1.html"), P1, "Mystery")
    assert len(books) == 20
    assert nxt == BASE + "catalogue/category/books/mystery_3/page-2.html"
    b = books[0]
    assert b.category == "Mystery"
    assert b.url.startswith(BASE + "catalogue/") and b.url.endswith("/index.html")
    assert isinstance(b.price, Decimal) and b.price > 0
    assert 1 <= b.rating <= 5
    assert b.in_stock is True


def test_list_page_last_has_no_next():
    books, nxt = parse_list_page(fixture_html("mystery_p2.html"), BASE + "catalogue/category/books/mystery_3/page-2.html", "Mystery")
    assert len(books) == 12
    assert nxt is None


def test_detail():
    upc, stock = parse_detail(fixture_html("detail_sharp_objects.html"))
    assert upc == "e00eb4fd7b871a48"
    assert stock == 20


def test_broken_page_is_reported():
    with pytest.raises(ParseError):
        parse_categories("<html><body>メンテナンス中</body></html>", BASE)
    html = '<article class="product_pod"><h3><a href="x" title="t">t</a></h3></article>'
    with pytest.raises(ParseError):
        parse_list_page(html, BASE, "X")
