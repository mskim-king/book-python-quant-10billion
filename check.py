#!/usr/bin/env python3
"""갱신이 필요한 페이지를 찾아 보고서(마크다운)로 출력합니다.

- '최종 확인' 날짜가 book.review_days 일보다 오래된 페이지
- (프롬프트 레시피) '마지막 테스트' 날짜가 book.retest_days 일보다 오래된 페이지
- 상태가 '완료'가 아닌 페이지 수

사용법:
    python check.py               # 화면에 보고서 출력
    python check.py --out r.md    # 파일로 저장 (GitHub Actions 에서 Issue 본문으로 사용)
종료 코드: 갱신 필요 페이지가 있으면 1, 없으면 0
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
REVIEW_RE = re.compile(r"\*\*최종 확인\*\*:\s*(\d{4}-\d{2}-\d{2})")
RETEST_RE = re.compile(r"\*\*마지막 테스트\*\*:\s*(\d{4}-\d{2}-\d{2})")
STATUS_RE = re.compile(r"\*\*상태\*\*:\s*([^\n]+?)\s*$", re.M)


def age(text: str, pattern: re.Pattern, today: dt.date) -> int | None:
    m = pattern.search(text)
    return (today - dt.date.fromisoformat(m.group(1))).days if m else None


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--out")
    args = ap.parse_args()

    data = yaml.safe_load((ROOT / "structure.yaml").read_text(encoding="utf-8"))
    book = data["book"]
    review_days = int(book.get("review_days", 90))
    retest_days = int(book.get("retest_days", 60))
    today = dt.date.today()

    stale, retest, drafts = [], [], 0
    for ch in data["chapters"]:
        for i, p in enumerate(ch.get("pages", []), 1):
            rel = f"pages/{ch['id']}-{i}-{p['slug']}.md"
            f = ROOT / rel
            if not f.exists():
                continue
            text = f.read_text(encoding="utf-8")
            st = STATUS_RE.search(text)
            if not (st and "완료" in st.group(1)):
                drafts += 1
                continue  # 작성 중인 글은 갱신 점검 대상 아님
            a = age(text, REVIEW_RE, today)
            if a is not None and a > review_days:
                stale.append((rel, p["title"], a))
            r = age(text, RETEST_RE, today)
            if r is not None and r > retest_days:
                retest.append((rel, p["title"], r))

    lines = [f"# 갱신 점검 보고서 ({today.isoformat()})", "",
             f"- 기준: 최종 확인 {review_days}일 / 프롬프트 재테스트 {retest_days}일",
             f"- 작성 중 페이지: {drafts}개", ""]
    if stale:
        lines += ["## 📅 내용 재확인 필요", ""]
        lines += [f"- [ ] `{r}` {t} — {a}일 경과" for r, t, a in stale] + [""]
    if retest:
        lines += ["## 🧪 프롬프트 재테스트 필요", ""]
        lines += [f"- [ ] `{r}` {t} — {a}일 경과" for r, t, a in retest] + [""]
    if not (stale or retest):
        lines.append("✅ 갱신이 필요한 완료 페이지가 없습니다.")
    report = "\n".join(lines) + "\n"

    if args.out:
        Path(args.out).write_text(report, encoding="utf-8")
    print(report)
    sys.exit(1 if (stale or retest) else 0)


if __name__ == "__main__":
    main()
