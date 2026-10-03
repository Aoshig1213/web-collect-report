"""設定ファイル（YAML）の読み込みと検証。"""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

import yaml


class ConfigError(Exception):
    """設定ファイルの内容に問題があるとき。"""


@dataclass
class Config:
    base_url: str = "https://books.toscrape.com/"
    # 集めるカテゴリ名（サイトの表示名）。空なら全カテゴリ
    categories: list[str] = field(default_factory=list)
    # 1回のリクエストのあとに待つ秒数（相手のサーバーに負荷をかけないため）
    delay_seconds: float = 1.0
    timeout_seconds: float = 15.0
    max_retries: int = 3
    # 詳細ページ（在庫数・商品コード）まで取りに行くか。行くと件数ぶん時間がかかる
    fetch_details: bool = False
    user_agent: str = "web-collect-report/1.0 (+https://github.com/Aoshig1213/web-collect-report)"
    output_dir: Path = Path("output")
    log_dir: Path = Path("logs")
    # Slack・Teams・Discord などの Incoming Webhook の URL。空なら通知しない
    webhook_url: str = ""


def load_config(path: Path) -> Config:
    if not path.exists():
        raise ConfigError(f"設定ファイルが見つかりません: {path}")
    try:
        raw = yaml.safe_load(path.read_text(encoding="utf-8")) or {}
    except yaml.YAMLError as e:
        raise ConfigError(f"設定ファイルの書き方に誤りがあります: {e}") from e
    if not isinstance(raw, dict):
        raise ConfigError("設定ファイルの一番上は「キー: 値」の形にしてください")

    known = set(Config.__dataclass_fields__)
    unknown = sorted(set(raw) - known)
    if unknown:
        raise ConfigError(f"知らない設定項目があります: {', '.join(unknown)}")

    cfg = Config(**raw)
    base = path.parent
    cfg.output_dir = (base / cfg.output_dir) if not Path(cfg.output_dir).is_absolute() else Path(cfg.output_dir)
    cfg.log_dir = (base / cfg.log_dir) if not Path(cfg.log_dir).is_absolute() else Path(cfg.log_dir)
    cfg.categories = [str(c) for c in (cfg.categories or [])]
    cfg.webhook_url = cfg.webhook_url or ""

    if not cfg.base_url.startswith(("http://", "https://")):
        raise ConfigError("base_url は http:// か https:// で始めてください")
    if not cfg.base_url.endswith("/"):
        cfg.base_url += "/"
    if cfg.delay_seconds < 0.5:
        raise ConfigError("delay_seconds は 0.5 以上にしてください（相手のサーバーへの負荷を抑えるため）")
    if cfg.max_retries < 0:
        raise ConfigError("max_retries は 0 以上にしてください")
    return cfg
