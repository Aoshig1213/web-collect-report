import requests

from webcollect import notify


def test_message_first_run():
    m = notify.build_message(1000, None, "report.xlsx")
    assert "1000件" in m and "初回" in m


def test_message_with_changes():
    m = notify.build_message(10, {"新規": 2, "値上げ": 0, "在庫切れ": 1}, "r.xlsx")
    assert "新規 2件" in m and "在庫切れ 1件" in m and "値上げ" not in m


def test_send_skips_without_url(monkeypatch):
    called = []
    monkeypatch.setattr(requests, "post", lambda *a, **k: called.append(a))
    assert notify.send("", "x") is False and called == []


def test_send_failure_does_not_raise(monkeypatch):
    def boom(*a, **k):
        raise requests.ConnectionError("つながらない")
    monkeypatch.setattr(requests, "post", boom)
    assert notify.send("https://hooks.example.com/x", "x") is False
