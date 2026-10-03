"""実行結果を Webhook（Slack・Teams・Discord など）に送る。失敗しても集計自体は止めない。"""

from __future__ import annotations

import logging

import requests

log = logging.getLogger(__name__)


def build_message(count: int, changes_summary: dict[str, int] | None, report_name: str) -> str:
    lines = [f"Web データ収集が終わりました（{count}件）", f"レポート: {report_name}"]
    if changes_summary is None:
        lines.append("初回のため、前回との比較はありません")
    elif not any(changes_summary.values()):
        lines.append("前回から変わったところはありません")
    else:
        lines.append("前回からの変化: " + "、".join(f"{k} {v}件" for k, v in changes_summary.items() if v))
    return "\n".join(lines)


def send(webhook_url: str, text: str, timeout: float = 10.0) -> bool:
    if not webhook_url:
        return False
    try:
        # Slack と Teams は "text"、Discord は "content" を読む
        r = requests.post(webhook_url, json={"text": text, "content": text}, timeout=timeout)
        r.raise_for_status()
        return True
    except requests.RequestException as e:
        log.warning("通知を送れませんでした（集計は完了しています）: %s", e)
        return False
