from datetime import datetime
from decimal import Decimal

from openpyxl import load_workbook

from webcollect.diff import Change
from webcollect.parser import Book
from webcollect.report import build_report


def books():
    return [Book(f"u{i}", f"本{i}", "Mystery" if i % 2 else "Travel", Decimal("10.50") + i, i % 5 + 1, i % 3 != 0) for i in range(10)]


def test_first_run_report(tmp_path):
    p = build_report(books(), None, tmp_path / "r.xlsx", source="https://example.com/", run_at=datetime(2026, 10, 4, 9, 30), has_previous=False)
    wb = load_workbook(p)
    assert wb.sheetnames == ["概要", "一覧", "カテゴリ別", "評価別", "前回との差分"]
    s = wb["一覧"]
    assert s.max_row == 11 and s["A1"].value == "書名" and s["C2"].value == 10.5
    assert wb["カテゴリ別"]["B2"].value == 5
    assert sum(wb["評価別"].cell(row=r, column=2).value for r in range(2, 7)) == 10
    assert "初回" in wb["前回との差分"]["A2"].value
    assert len(wb["カテゴリ別"]._charts) == 1 and len(wb["評価別"]._charts) == 1


def test_report_with_changes(tmp_path):
    ch = [Change("値上げ", "本1", "u1", "£10.50", "£12.00"), Change("新規", "本9", "u9", "", "£19.50")]
    p = build_report(books(), ch, tmp_path / "r.xlsx", source="s", run_at=datetime(2026, 10, 4), has_previous=True)
    ws = load_workbook(p)["前回との差分"]
    assert [ws.cell(row=r, column=1).value for r in (2, 3)] == ["値上げ", "新規"]
    summary = {r[0].value: r[1].value for r in load_workbook(p)["概要"].iter_rows(min_row=3)}
    assert summary["前回からの値上げ"] == 1 and summary["前回からの新規"] == 1


def test_report_no_changes(tmp_path):
    p = build_report(books(), [], tmp_path / "r.xlsx", source="s", run_at=datetime(2026, 10, 4), has_previous=True)
    assert "変わったところはありません" in load_workbook(p)["前回との差分"]["A2"].value
