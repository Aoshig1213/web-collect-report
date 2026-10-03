"""カテゴリをたどって全ページを集める。"""

from __future__ import annotations

import logging

from webcollect.fetcher import Fetcher
from webcollect.parser import Book, parse_categories, parse_detail, parse_list_page

log = logging.getLogger(__name__)


def collect(fetcher: Fetcher, base_url: str, categories: list[str], fetch_details: bool,
            max_pages_per_category: int = 100) -> list[Book]:
    home = base_url + "index.html"
    all_cats = parse_categories(fetcher.get(home), home)
    if categories:
        missing = [c for c in categories if c not in all_cats]
        if missing:
            raise ValueError(f"サイトにないカテゴリが指定されています: {', '.join(missing)}")
        targets = {c: all_cats[c] for c in categories}
    else:
        targets = all_cats
    log.info("カテゴリ %d 件を集めます", len(targets))

    books: dict[str, Book] = {}
    for i, (cat, url) in enumerate(targets.items(), 1):
        pages = 0
        while url and pages < max_pages_per_category:
            found, url = parse_list_page(fetcher.get(url), url, cat)
            for b in found:
                books.setdefault(b.url, b)  # 同じ本が2つのカテゴリに出ても1件として数える
            pages += 1
        log.info("[%d/%d] %s: %dページ", i, len(targets), cat, pages)

    if fetch_details:
        for j, b in enumerate(books.values(), 1):
            b.upc, b.stock_count = parse_detail(fetcher.get(b.url))
            if j % 50 == 0:
                log.info("詳細ページ %d/%d", j, len(books))
    return list(books.values())
