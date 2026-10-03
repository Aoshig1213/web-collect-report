"""README 用に「前回との差分」の見え方を再現する。

練習用サイトは中身が変わらないため、最新の履歴を少し書き換えたものを「前回」として比べる。
使い方: python tools/demo_diff.py <最新の snapshot_*.csv> <出力先.xlsx>
"""

import sys
from dataclasses import replace
from datetime import datetime
from decimal import Decimal
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))

from webcollect.diff import diff  # noqa: E402
from webcollect.report import build_report  # noqa: E402
from webcollect.storage import load_snapshot  # noqa: E402

cur = load_snapshot(Path(sys.argv[1]))
prev = [replace(b) for b in cur]
prev[0].price += Decimal("3.00")        # 今回は値下げに見える
prev[1].price -= Decimal("2.50")        # 今回は値上げに見える
prev[2].in_stock = False                # 今回は再入荷に見える
del prev[3]                             # 今回は新規に見える
prev.append(replace(cur[4], url=cur[4].url.replace("index.html", "old.html"), title="（前回だけあった本の例）"))  # 掲載終了
build_report(cur, diff(prev, cur), Path(sys.argv[2]), source="https://books.toscrape.com/（差分の見本）",
             run_at=datetime.now(), has_previous=True)
print(sys.argv[2])
