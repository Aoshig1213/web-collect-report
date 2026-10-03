"""books.toscrape.com のページから必要な項目を取り出す。"""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from urllib.parse import urljoin

from bs4 import BeautifulSoup

RATING = {"One": 1, "Two": 2, "Three": 3, "Four": 4, "Five": 5}


class ParseError(Exception):
    """ページの形が想定と違うとき（サイトのデザインが変わったなど）。"""


@dataclass
class Book:
    url: str
    title: str
    category: str
    price: Decimal
    rating: int
    in_stock: bool
    stock_count: int | None = None
    upc: str | None = None


def parse_categories(html: str, page_url: str) -> dict[str, str]:
    """トップページの左側の一覧から {カテゴリ名: URL}。"""
    soup = BeautifulSoup(html, "html.parser")
    links = soup.select("div.side_categories ul li ul li a")
    if not links:
        raise ParseError("カテゴリの一覧が見つかりません")
    return {a.get_text(strip=True): urljoin(page_url, a["href"]) for a in links}


def _price(text: str) -> Decimal:
    m = re.search(r"(\d+(?:\.\d+)?)", text.replace(",", ""))
    if not m:
        raise ParseError(f"価格が読めません: {text!r}")
    try:
        return Decimal(m.group(1))
    except InvalidOperation as e:
        raise ParseError(f"価格が読めません: {text!r}") from e


def parse_list_page(html: str, page_url: str, category: str) -> tuple[list[Book], str | None]:
    """一覧ページの本と、次のページの URL（なければ None）。"""
    soup = BeautifulSoup(html, "html.parser")
    books = []
    for pod in soup.select("article.product_pod"):
        a = pod.select_one("h3 a")
        price = pod.select_one("p.price_color")
        star = pod.select_one("p.star-rating")
        avail = pod.select_one("p.availability")
        if not (a and price and star and avail):
            raise ParseError(f"本の情報が欠けています: {page_url}")
        rating = next((RATING[c] for c in star.get("class", []) if c in RATING), None)
        if rating is None:
            raise ParseError(f"評価が読めません: {star.get('class')}")
        books.append(Book(
            url=urljoin(page_url, a["href"]),
            title=a.get("title") or a.get_text(strip=True),
            category=category,
            price=_price(price.get_text()),
            rating=rating,
            in_stock="in stock" in avail.get_text().lower(),
        ))
    nxt = soup.select_one("li.next a")
    return books, (urljoin(page_url, nxt["href"]) if nxt else None)


def parse_detail(html: str) -> tuple[str | None, int | None]:
    """詳細ページの商品コード（UPC）と在庫数。"""
    soup = BeautifulSoup(html, "html.parser")
    info = {th.get_text(strip=True): td.get_text(strip=True)
            for th, td in ((tr.th, tr.td) for tr in soup.select("table.table-striped tr")) if th and td}
    m = re.search(r"\((\d+) available\)", info.get("Availability", ""))
    return info.get("UPC"), (int(m.group(1)) if m else (0 if "Out of stock" in info.get("Availability", "") else None))
