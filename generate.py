#!/usr/bin/env python3
"""structure.yaml 을 읽어 위키독스(GitHub 연동) 책 구조를 자동 생성합니다.

위키독스 GitHub 연동 형식 (pahkey/github-wikidocs 기준):
- TOC.md : '# 목차' + '- [제목](pages/파일.md)' , 하위는 2칸 들여쓰기 (같은 단계는 제목 이름순 정렬)
- pages/ : 모든 페이지를 한 폴더에 (01-장.md, 01-1-페이지.md ...)
- 페이지 본문에는 H1 제목을 쓰지 않음 (제목은 TOC 에서 가져옴)
- README.md : 독자에게 보이는 책 소개
- assets/ : 이미지 (페이지에서는 ../assets/파일.png, README 에서는 ./assets/파일.png)

사용법:
    python generate.py            # 페이지 생성 + TOC.md / README.md / 진행현황 갱신
    python generate.py --check    # 미리 보기 (파일 변경 없음)
    python generate.py --status   # 페이지별 작성 상태 표시

규칙:
- 이미 존재하는 페이지 파일은 절대 덮어쓰지 않습니다.
- 공개 범위: 상태가 '작성 중'인 페이지는 TOC 에 넣지 않습니다 (독자에게 안 보임).
  structure.yaml 의 book.show_drafts: true 로 바꾸면 모든 페이지를 공개합니다.
- structure.yaml 에서 빠진 파일은 지우지 않고 '고아 파일'로 알려줍니다.
"""
from __future__ import annotations

import argparse
import datetime as dt
import re
import sys
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent
TEMPLATES = ROOT / "templates"
PAGES = "pages"
STATUS_RE = re.compile(r"\*\*상태\*\*:\s*([^\n]+?)\s*$", re.M)
DRAFT = "작성 중"


def load_structure() -> dict:
    with open(ROOT / "structure.yaml", encoding="utf-8") as f:
        data = yaml.safe_load(f)
    seen = set()
    for ch in data["chapters"]:
        for key in ("id", "slug", "title"):
            if key not in ch:
                sys.exit(f"[오류] 장(chapter)에 '{key}' 가 없습니다: {ch}")
        for i, p in enumerate(ch.get("pages", []), 1):
            path = page_path(ch, i, p)
            if path in seen:
                sys.exit(f"[오류] 중복 페이지 경로: {path}")
            seen.add(path)
            if not (TEMPLATES / f"{p.get('template', 'page')}.md").exists():
                sys.exit(f"[오류] 템플릿 없음: {p.get('template')} ({path})")
    return data


# ---------- 경로와 제목 ----------
def chapter_path(ch: dict) -> str:
    return f"{PAGES}/{ch['id']}-{ch['slug']}.md"


def chapter_title(ch: dict) -> str:
    return f"{ch['id']}. {ch['title']}"


def page_path(ch: dict, i: int, p: dict) -> str:
    return f"{PAGES}/{ch['id']}-{i}-{p['slug']}.md"


def page_title(ch: dict, i: int, p: dict) -> str:
    return f"{ch['id']}-{i}. {p['title']}"


def iter_pages(data: dict):
    for ch in data["chapters"]:
        for i, p in enumerate(ch.get("pages", []), 1):
            yield ch, i, p


# ---------- 렌더링 ----------
def render(template: str, **kw) -> str:
    text = (TEMPLATES / template).read_text(encoding="utf-8")
    for k, v in kw.items():
        text = text.replace("{" + k + "}", str(v))
    return text


def related_links(ch: dict, current: dict) -> str:
    lines = [f"- {ch['id']}-{i}. {p['title']}"
             for i, p in enumerate(ch.get("pages", []), 1) if p["slug"] != current["slug"]]
    for link in current.get("see_also", []):
        lines.append(f"- 📚 『{link}』")
    return "\n".join(lines) or "- "


def read_status(path: Path) -> str:
    if not path.exists():
        return "⚪ 없음"
    m = STATUS_RE.search(path.read_text(encoding="utf-8"))
    return m.group(1).strip() if m else "❔ 미표시"


def is_public(status: str, show_drafts: bool) -> bool:
    return show_drafts or (DRAFT not in status and "없음" not in status)


def build_toc(data: dict, statuses: dict[str, str]) -> str:
    show = bool(data["book"].get("show_drafts", False))
    lines = ["# 목차", ""]
    for ch in data["chapters"]:
        children = [
            f"  - [{page_title(ch, i, p)}]({page_path(ch, i, p)})"
            for i, p in enumerate(ch.get("pages", []), 1)
            if is_public(statuses[page_path(ch, i, p)], show)
        ]
        if children or show:
            lines.append(f"- [{chapter_title(ch)}]({chapter_path(ch)})")
            lines += children
    return "\n".join(lines) + "\n"


def build_readme(data: dict) -> str:
    """독자에게 보이는 책 소개 (위키독스 책 첫 화면)."""
    b = data["book"]
    out = [f"# {b['title']}", ""]
    if (ROOT / "assets" / "cover.png").exists():  # 표지 (tools/build_cover.py 로 생성)
        out += [f"![{b['title']} 표지](./assets/cover.png)", ""]
    out += [f"**{b.get('subtitle', '')}**", "", b.get("description", "").strip(), ""]
    if b.get("audience"):
        out += ["## 이런 분께 추천합니다", ""]
        out += [f"- {a.strip()}" for a in str(b["audience"]).split(",")] + [""]
    out += ["## 이 책의 구성", "", "| 장 | 내용 |", "|---|---|"]
    for ch in data["chapters"]:
        out.append(f"| {chapter_title(ch)} | {ch.get('summary', '')} |")
    out.append("")
    series = data.get("series")
    if series:
        others = [s for s in series.get("books", []) if s["title"] != b["title"]]
        out += [f"## 「{series['name']}」 시리즈", ""]
        if series.get("url"):
            out += [f"시리즈 전체 소개: [{series['name']}]({series['url']})", ""]
        out += [f"- [{s['title']}]({s['url']})" if s.get("url") else f"- {s['title']} (준비 중)" for s in others]
        out.append("")
    if b.get("author"):
        out += ["## 저자", "", f"{b['author']}", ""]
    return "\n".join(out)


def build_progress(data: dict, statuses: dict[str, str]) -> str:
    """관리용 진행 현황 (위키독스에 공개되지 않음)."""
    show = bool(data["book"].get("show_drafts", False))
    total = len(statuses)
    done = sum("완료" in s for s in statuses.values())
    public = sum(is_public(s, show) for s in statuses.values())
    out = [f"# 진행 현황 ({dt.date.today().isoformat()})", "",
           f"- 완료 {done} / 전체 {total} · 위키독스 공개 {public}개", "",
           "| 페이지 | 파일 | 상태 | 공개 |", "|---|---|---|---|"]
    for ch, i, p in iter_pages(data):
        path = page_path(ch, i, p)
        st = statuses[path]
        out.append(f"| {page_title(ch, i, p)} | `{path}` | {st} | {'✅' if is_public(st, show) else '—'} |")
    return "\n".join(out) + "\n"


# ---------- 메인 ----------
def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--check", action="store_true", help="변경 없이 미리 보기")
    ap.add_argument("--status", action="store_true", help="페이지 상태만 출력")
    args = ap.parse_args()
    dry = args.check or args.status

    data = load_structure()
    today = dt.date.today().isoformat()
    created, expected = [], set()
    if not dry:
        (ROOT / PAGES).mkdir(exist_ok=True)
        (ROOT / "assets").mkdir(exist_ok=True)
        (ROOT / "assets" / ".gitkeep").touch()

    for ch in data["chapters"]:
        cpath = chapter_path(ch)
        expected.add(cpath)
        if not (ROOT / cpath).exists():
            created.append(cpath)
            if not dry:
                page_list = "\n".join(f"- {page_title(ch, i, p)}" for i, p in enumerate(ch.get("pages", []), 1))
                (ROOT / cpath).write_text(render("chapter.md",
                                                 chapter_summary=ch.get("summary", "이 장에서 다루는 내용입니다."),
                                                 page_list=page_list), encoding="utf-8")
    for ch, i, p in iter_pages(data):
        rel = page_path(ch, i, p)
        expected.add(rel)
        if (ROOT / rel).exists():
            continue
        # 페이지 순서가 바뀌어 번호만 달라진 경우: 기존 파일을 새 번호로 이동 (내용 보존)
        moved = [m for m in (ROOT / PAGES).glob(f"{ch['id']}-*-{p['slug']}.md") if m.exists()] \
            if (ROOT / PAGES).exists() else []
        if len(moved) == 1:
            print(f"  ↪ 이동: {moved[0].relative_to(ROOT)} → {rel}")
            if not dry:
                moved[0].rename(ROOT / rel)
            continue
        created.append(rel)
        if dry:
            continue
        (ROOT / rel).write_text(render(f"{p.get('template', 'page')}.md",
                                       chapter_title=chapter_title(ch),
                                       tags=" ".join(f"#{t}" for t in p.get("tags", [])),
                                       date=today,
                                       related=related_links(ch, p)), encoding="utf-8")

    statuses = {page_path(ch, i, p): read_status(ROOT / page_path(ch, i, p)) for ch, i, p in iter_pages(data)}

    if args.status:
        for path, st in statuses.items():
            print(f"{st:<10} {path}")
        return

    orphans = sorted(str(p.relative_to(ROOT)) for p in (ROOT / PAGES).glob("*.md")
                     if str(p.relative_to(ROOT)) not in expected) if (ROOT / PAGES).exists() else []

    if not args.check:
        (ROOT / "TOC.md").write_text(build_toc(data, statuses), encoding="utf-8")
        (ROOT / "README.md").write_text(build_readme(data), encoding="utf-8")
        (ROOT / "_관리").mkdir(exist_ok=True)
        (ROOT / "_관리" / "진행현황.md").write_text(build_progress(data, statuses), encoding="utf-8")

    label = "생성 예정" if args.check else "새로 생성"
    print(f"[{label}] {len(created)}개")
    for c in created:
        print(f"  + {c}")
    if orphans:
        print(f"[고아 파일] structure.yaml 에 없는 파일 {len(orphans)}개 (삭제하지 않음)")
        for o in orphans:
            print(f"  ? {o}")
    if not args.check:
        public = sum(is_public(s, bool(data['book'].get('show_drafts'))) for s in statuses.values())
        print(f"[갱신] TOC.md(공개 페이지 {public}개), README.md, _관리/진행현황.md")


if __name__ == "__main__":
    main()
