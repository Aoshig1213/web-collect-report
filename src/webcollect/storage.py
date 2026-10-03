"""集めた結果を CSV（履歴）として保存し、前回分を読み出す。"""

from __future__ import annotations

import csv
from datetime import datetime
from decimal import Decimal
from pathlib import Path

from webcollect.parser import Book

FIELDS = ["url", "title", "category", "price", "rating", "in_stock", "stock_count", "upc"]


def save_snapshot(books: list[Book], history_dir: Path, now: datetime) -> Path:
    history_dir.mkdir(parents=True, exist_ok=True)
    path = history_dir / f"snapshot_{now:%Y%m%d_%H%M%S}.csv"
    # Excel でそのまま開けるよう BOM 付き UTF-8
    with path.open("w", newline="", encoding="utf-8-sig") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS)
        w.writeheader()
        for b in books:
            w.writerow({"url": b.url, "title": b.title, "category": b.category, "price": str(b.price),
                        "rating": b.rating, "in_stock": int(b.in_stock),
                        "stock_count": "" if b.stock_count is None else b.stock_count, "upc": b.upc or ""})
    return path


def load_snapshot(path: Path) -> list[Book]:
    with path.open(newline="", encoding="utf-8-sig") as f:
        return [Book(url=r["url"], title=r["title"], category=r["category"], price=Decimal(r["price"]),
                     rating=int(r["rating"]), in_stock=r["in_stock"] == "1",
                     stock_count=int(r["stock_count"]) if r["stock_count"] else None, upc=r["upc"] or None)
                for r in csv.DictReader(f)]


def previous_snapshot(history_dir: Path, current: Path | None = None) -> Path | None:
    """current より前の、いちばん新しい履歴。"""
    files = sorted(p for p in history_dir.glob("snapshot_*.csv") if p != current)
    if current is not None:
        files = [p for p in files if p.name < current.name]
    return files[-1] if files else None
