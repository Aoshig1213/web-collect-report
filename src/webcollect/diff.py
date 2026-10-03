"""前回と今回の違い（新規・掲載終了・価格・在庫）を出す。"""

from __future__ import annotations

from dataclasses import dataclass

from webcollect.parser import Book

ORDER = ["新規", "掲載終了", "値上げ", "値下げ", "在庫切れ", "再入荷", "在庫数の変化"]


@dataclass
class Change:
    kind: str
    title: str
    url: str
    before: str = ""
    after: str = ""


def diff(prev: list[Book], cur: list[Book]) -> list[Change]:
    old = {b.url: b for b in prev}
    new = {b.url: b for b in cur}
    out: list[Change] = []
    for url, b in new.items():
        a = old.get(url)
        if a is None:
            out.append(Change("新規", b.title, url, "", f"£{b.price}"))
            continue
        if b.price != a.price:
            out.append(Change("値上げ" if b.price > a.price else "値下げ", b.title, url, f"£{a.price}", f"£{b.price}"))
        if a.in_stock and not b.in_stock:
            out.append(Change("在庫切れ", b.title, url, "在庫あり", "在庫なし"))
        elif not a.in_stock and b.in_stock:
            out.append(Change("再入荷", b.title, url, "在庫なし", "在庫あり"))
        elif a.stock_count is not None and b.stock_count is not None and a.stock_count != b.stock_count:
            out.append(Change("在庫数の変化", b.title, url, str(a.stock_count), str(b.stock_count)))
    for url, a in old.items():
        if url not in new:
            out.append(Change("掲載終了", a.title, url, f"£{a.price}", ""))
    out.sort(key=lambda c: (ORDER.index(c.kind), c.title))
    return out
