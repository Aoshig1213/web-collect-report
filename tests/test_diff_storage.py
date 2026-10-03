from datetime import datetime
from decimal import Decimal

from webcollect.diff import diff
from webcollect.parser import Book
from webcollect.storage import load_snapshot, previous_snapshot, save_snapshot


def book(url, price="10.00", in_stock=True, stock=None, title=None):
    return Book(url=url, title=title or url, category="C", price=Decimal(price), rating=3, in_stock=in_stock, stock_count=stock)


def test_diff_kinds():
    prev = [book("a", "10.00"), book("b", "10.00"), book("c"), book("d", in_stock=False), book("e", stock=5), book("gone")]
    cur = [book("a", "12.50"), book("b", "9.99"), book("c", in_stock=False), book("d"), book("e", stock=3), book("new")]
    kinds = {(c.kind, c.url) for c in diff(prev, cur)}
    assert kinds == {("値上げ", "a"), ("値下げ", "b"), ("在庫切れ", "c"), ("再入荷", "d"), ("在庫数の変化", "e"),
                     ("新規", "new"), ("掲載終了", "gone")}


def test_diff_no_change():
    bs = [book("a"), book("b")]
    assert diff(bs, list(bs)) == []


def test_diff_order_new_first():
    out = diff([book("x", "1"), book("gone")], [book("x", "2"), book("new")])
    assert [c.kind for c in out] == ["新規", "掲載終了", "値上げ"]


def test_snapshot_roundtrip_and_previous(tmp_path):
    h = tmp_path / "history"
    b1 = [book("a", "10.00", stock=4, title="ゼロから学ぶ, \"引用\"付き"), book("b", in_stock=False)]
    p1 = save_snapshot(b1, h, datetime(2026, 10, 1, 9, 0, 0))
    p2 = save_snapshot([book("a")], h, datetime(2026, 10, 2, 9, 0, 0))
    assert load_snapshot(p1) == b1
    assert previous_snapshot(h, p2) == p1
    assert previous_snapshot(h, p1) is None
