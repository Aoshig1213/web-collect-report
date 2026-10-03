"""コマンドの入口。  例: python -m webcollect --config config.yaml"""

from __future__ import annotations

import argparse
import logging
import sys
from collections import Counter
from datetime import datetime
from logging.handlers import RotatingFileHandler
from pathlib import Path

from webcollect import __version__, notify
from webcollect.collector import collect
from webcollect.config import ConfigError, load_config
from webcollect.diff import ORDER, diff
from webcollect.fetcher import Fetcher, FetchError
from webcollect.parser import ParseError
from webcollect.report import build_report
from webcollect.storage import load_snapshot, previous_snapshot, save_snapshot

log = logging.getLogger("webcollect")


def _default_config() -> Path:
    # exe にしたときは exe と同じフォルダの config.yaml を読む
    base = Path(sys.executable).parent if getattr(sys, "frozen", False) else Path.cwd()
    return base / "config.yaml"


def _setup_logging(log_dir: Path) -> None:
    log_dir.mkdir(parents=True, exist_ok=True)
    fmt = logging.Formatter("%(asctime)s %(levelname)s %(message)s", "%Y-%m-%d %H:%M:%S")
    fh = RotatingFileHandler(log_dir / "webcollect.log", maxBytes=1_000_000, backupCount=5, encoding="utf-8")
    fh.setFormatter(fmt)
    sh = logging.StreamHandler()
    sh.setFormatter(fmt)
    root = logging.getLogger()
    root.handlers[:] = [fh, sh]
    root.setLevel(logging.INFO)


def main(argv: list[str] | None = None) -> int:
    ap = argparse.ArgumentParser(prog="webcollect", description="Web の商品一覧を集めて Excel レポートにします")
    ap.add_argument("--config", type=Path, default=None, help="設定ファイル（省略時は config.yaml）")
    ap.add_argument("--categories", nargs="*", help="集めるカテゴリ（設定ファイルより優先）")
    ap.add_argument("--details", action="store_true", help="詳細ページ（在庫数・商品コード）も取る")
    ap.add_argument("--no-notify", action="store_true", help="通知を送らない")
    ap.add_argument("--version", action="version", version=f"%(prog)s {__version__}")
    args = ap.parse_args(argv)

    try:
        cfg = load_config(args.config or _default_config())
    except ConfigError as e:
        print(f"設定エラー: {e}", file=sys.stderr)
        return 2
    if args.categories is not None:
        cfg.categories = args.categories
    if args.details:
        cfg.fetch_details = True
    _setup_logging(cfg.log_dir)

    run_at = datetime.now()
    log.info("開始します（%s）", cfg.base_url)
    fetcher = Fetcher(cfg.user_agent, cfg.delay_seconds, cfg.timeout_seconds, cfg.max_retries)
    try:
        books = collect(fetcher, cfg.base_url, cfg.categories, cfg.fetch_details)
    except (FetchError, ParseError, ValueError) as e:
        log.error("中止しました: %s", e)
        return 1
    if not books:
        log.error("1件も取れませんでした。サイトの形が変わった可能性があります")
        return 1

    history = cfg.output_dir / "history"
    snap = save_snapshot(books, history, run_at)
    prev = previous_snapshot(history, snap)
    changes = diff(load_snapshot(prev), books) if prev else None
    report = build_report(books, changes, cfg.output_dir / f"report_{run_at:%Y%m%d_%H%M}.xlsx",
                          source=cfg.base_url, run_at=run_at, has_previous=prev is not None)
    summary = None if changes is None else {k: v for k, v in sorted(Counter(c.kind for c in changes).items(), key=lambda kv: ORDER.index(kv[0]))}
    log.info("完了: %d件、リクエスト %d回、レポート %s", len(books), fetcher.count, report)
    if summary:
        log.info("前回からの変化: %s", summary)
    if not args.no_notify and cfg.webhook_url:
        notify.send(cfg.webhook_url, notify.build_message(len(books), summary, report.name))
    return 0
