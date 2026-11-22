#!/usr/bin/env python3
"""tools/diagrams.yaml 에 정의한 설명 이미지를 assets/*.png 로 만듭니다. (디자인 v2)

사용법:
    python tools/build_diagrams.py            # 전체 다시 만들기
    python tools/build_diagrams.py ch01       # 파일 이름에 'ch01' 이 들어간 것만

layout 종류
    flow     단계 흐름 (steps)
    cards    카드 묶음 (cards, columns)
    compare  나쁜 예 → 좋은 예 (left, right)
    matrix   2x2 판단표 (x_axis, y_axis, cells)
    spectrum 왼쪽→오른쪽 연속 스펙트럼 (items, left_label, right_label)
    triple   그래프 관계 (rows: [주어, 관계, 목적어])
    stack    아래에서 위로 쌓이는 계층 (layers: 위층이 먼저)

필요한 것: Python(pyyaml), Node.js + Playwright, 한글 글꼴(Noto Sans CJK KR), 이모지 글꼴(Noto Color Emoji)
"""
from __future__ import annotations

import html
import json
import subprocess
import sys
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
ASSETS = ROOT / "assets"

PALETTE = {  # 이름: (진한, 중간, 연한)
    "blue": ("#1D4ED8", "#3B82F6", "#EFF6FF"), "indigo": ("#4338CA", "#6366F1", "#EEF2FF"),
    "violet": ("#6D28D9", "#8B5CF6", "#F5F3FF"), "purple": ("#7E22CE", "#A855F7", "#FAF5FF"),
    "pink": ("#BE185D", "#EC4899", "#FDF2F8"), "red": ("#B91C1C", "#EF4444", "#FEF2F2"),
    "orange": ("#C2410C", "#F97316", "#FFF7ED"), "amber": ("#B45309", "#F59E0B", "#FFFBEB"),
    "green": ("#15803D", "#22C55E", "#F0FDF4"), "emerald": ("#047857", "#10B981", "#ECFDF5"),
    "teal": ("#0F766E", "#14B8A6", "#F0FDFA"), "cyan": ("#0E7490", "#06B6D4", "#ECFEFF"),
    "slate": ("#334155", "#64748B", "#F1F5F9"), "gray": ("#334155", "#64748B", "#F1F5F9"),
}


def pal(name: str | None, default: str) -> tuple[str, str, str]:
    return PALETTE.get(name or default, PALETTE[default])


def esc(s) -> str:
    return html.escape(str(s if s is not None else ""))


def css(theme: dict) -> str:
    p1, p2, p3 = pal(theme.get("primary"), "indigo")
    s1, s2, _ = pal(theme.get("secondary"), "cyan")
    return f"""
* {{ box-sizing: border-box; margin: 0; padding: 0; }}
body {{ background: #fff; font-family: 'Noto Sans CJK KR', sans-serif; color: #0F172A; -webkit-font-smoothing: antialiased; }}
#c {{ width: 1200px; padding: 44px 56px 34px; position: relative; overflow: hidden; background: #FFFFFF; }}
#c::before {{ content: ''; position: absolute; width: 620px; height: 620px; right: -220px; top: -330px;
  background: radial-gradient(circle, {p2}33 0%, transparent 65%); }}
#c::after {{ content: ''; position: absolute; width: 520px; height: 520px; left: -260px; bottom: -320px;
  background: radial-gradient(circle, {s2}26 0%, transparent 65%); }}
.z {{ position: relative; z-index: 1; }}
.kicker {{ display: inline-flex; align-items: center; gap: 10px; font-size: 15px; font-weight: 700; letter-spacing: 1.5px;
  color: {p1}; background: {p3}; border: 1px solid {p2}40; padding: 7px 14px; border-radius: 999px; }}
.kicker .dot {{ width: 8px; height: 8px; border-radius: 50%; background: linear-gradient(135deg, {p2}, {s2}); }}
h1 {{ margin-top: 16px; font-size: 42px; font-weight: 800; letter-spacing: -1px; line-height: 1.25; }}
h1 em {{ font-style: normal; background: linear-gradient(90deg, {p1}, {s1}); -webkit-background-clip: text; color: transparent; }}
.sub {{ margin-top: 10px; font-size: 21px; color: #475569; line-height: 1.5; }}
.body {{ margin-top: 34px; }}
.badge {{ width: 72px; height: 72px; border-radius: 22px; display: flex; align-items: center; justify-content: center;
  font-size: 36px; font-family: 'Noto Color Emoji', sans-serif; background: linear-gradient(135deg, var(--m), var(--d));
  box-shadow: 0 10px 20px -8px var(--m); }}
.badge span {{ filter: drop-shadow(0 2px 2px rgba(0,0,0,.15)); }}
.t {{ font-size: 23px; font-weight: 800; letter-spacing: -0.3px; color: var(--d); }}
.d {{ font-size: 17px; color: #475569; line-height: 1.55; white-space: pre-line; }}
.card {{ background: #fff; border-radius: 22px; padding: 26px 24px; border: 1px solid #E2E8F0;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 12px 28px -12px rgba(15,23,42,.18); position: relative; overflow: hidden; }}
.card::before {{ content: ''; position: absolute; left: 0; top: 0; right: 0; height: 5px; background: linear-gradient(90deg, var(--m), var(--d)); }}
.card .t {{ margin-top: 18px; }} .card .d {{ margin-top: 8px; }}
.grid {{ display: grid; gap: 22px; }}
/* flow */
.flow {{ display: flex; align-items: stretch; }}
.step {{ flex: 1; text-align: center; padding-top: 30px; }}
.step .badge {{ margin: 0 auto; }}
.step .t {{ margin-top: 16px; }} .step .d {{ margin-top: 8px; }}
.num {{ position: absolute; top: 14px; left: 16px; font-size: 14px; font-weight: 800; color: var(--m); letter-spacing: 1px; }}
.conn {{ width: 46px; flex: none; display: flex; align-items: center; justify-content: center; }}
.conn svg {{ width: 34px; height: 34px; }}
/* compare */
.cmp {{ display: grid; grid-template-columns: 1fr 64px 1fr; align-items: stretch; }}
.panel {{ border-radius: 22px; overflow: hidden; background: #fff; border: 1px solid #E2E8F0;
  box-shadow: 0 12px 28px -12px rgba(15,23,42,.18); }}
.panel h2 {{ font-size: 22px; font-weight: 800; color: #fff; padding: 18px 26px; display: flex; gap: 10px; align-items: center; }}
.panel ul {{ padding: 14px 22px 22px; }}
.panel li {{ list-style: none; font-size: 19px; line-height: 1.5; padding: 13px 16px; margin-top: 10px; border-radius: 12px;
  display: flex; gap: 12px; align-items: flex-start; }}
.panel li i {{ font-style: normal; font-weight: 800; flex: none; width: 24px; height: 24px; border-radius: 50%; color: #fff;
  font-size: 14px; display: flex; align-items: center; justify-content: center; margin-top: 3px; }}
.bad h2 {{ background: linear-gradient(90deg, #DC2626, #F43F5E); }} .bad li {{ background: #FEF2F2; }} .bad li i {{ background: #EF4444; }}
.good h2 {{ background: linear-gradient(90deg, #059669, #10B981); }} .good li {{ background: #ECFDF5; }} .good li i {{ background: #10B981; }}
.mid {{ display: flex; align-items: center; justify-content: center; }}
/* matrix */
.mx {{ display: grid; grid-template-columns: 190px 1fr 1fr; grid-template-rows: 54px 1fr 1fr; gap: 16px; }}
.ax {{ display: flex; align-items: center; justify-content: center; font-size: 18px; font-weight: 800; color: {p1};
  background: {p3}; border-radius: 14px; text-align: center; padding: 8px; }}
.cell {{ text-align: center; }} .cell .badge {{ margin: 0 auto; }} .cell .t {{ margin-top: 14px; }}
/* spectrum */
.spec-bar {{ height: 16px; border-radius: 999px; margin: 8px 0 26px; background: linear-gradient(90deg, #EF4444, #F59E0B, #10B981); position: relative; }}
.spec-labels {{ display: flex; justify-content: space-between; font-size: 16px; font-weight: 700; color: #64748B; }}
/* triple */
.trip {{ display: flex; flex-direction: column; gap: 18px; }}
.row {{ display: grid; grid-template-columns: 1fr 260px 1fr; align-items: center; }}
.node {{ border-radius: 999px; padding: 16px 22px; text-align: center; font-size: 21px; font-weight: 800; color: var(--d);
  background: var(--l); border: 2px solid var(--m); box-shadow: 0 10px 22px -14px var(--m); }}
.node small {{ display: block; font-size: 14px; font-weight: 600; color: #64748B; margin-top: 2px; }}
.edge {{ position: relative; text-align: center; font-size: 17px; font-weight: 700; color: #334155; }}
.edge::before {{ content: ''; position: absolute; left: 6px; right: 14px; top: 50%; height: 3px; background: linear-gradient(90deg, {p2}, {s2}); }}
.edge::after {{ content: ''; position: absolute; right: 4px; top: calc(50% - 8px); border: 9px solid transparent; border-left: 13px solid {s2}; border-right: 0; }}
.edge span {{ position: relative; background: #fff; padding: 4px 12px; border-radius: 999px; border: 1px solid #E2E8F0; }}
/* stack */
.stack {{ display: flex; flex-direction: column; gap: 12px; }}
.layer {{ display: grid; grid-template-columns: 72px 260px 1fr; gap: 22px; align-items: center; padding: 16px 22px;
  border-radius: 18px; background: #fff; border: 1px solid #E2E8F0; border-left: 8px solid var(--m);
  box-shadow: 0 10px 24px -16px rgba(15,23,42,.25); }}
.layer .badge {{ width: 60px; height: 60px; font-size: 30px; border-radius: 18px; }}
/* note & footer */
.note {{ margin-top: 30px; padding: 18px 24px; border-radius: 16px; display: flex; gap: 14px; align-items: center;
  background: linear-gradient(90deg, #0F172A, #1E293B); color: #F8FAFC; font-size: 19px; font-weight: 500; }}
.note .ic {{ font-family: 'Noto Color Emoji'; font-size: 24px; }}
.foot {{ margin-top: 22px; display: flex; justify-content: space-between; font-size: 13px; color: #94A3B8; font-weight: 600; letter-spacing: .5px; }}
"""


def vars_(color: str | None, default: str = "indigo") -> str:
    d, m, l = pal(color, default)
    return f"--d:{d};--m:{m};--l:{l}"


def badge(icon) -> str:
    return f'<div class="badge"><span>{esc(icon)}</span></div>'


ARROW = ('<svg viewBox="0 0 24 24" fill="none"><path d="M5 12h12m-5-6 6 6-6 6" stroke="#94A3B8" '
         'stroke-width="2.6" stroke-linecap="round" stroke-linejoin="round"/></svg>')


def flow(d, th):
    out = []
    for i, s in enumerate(d["steps"], 1):
        if i > 1:
            out.append(f'<div class="conn">{ARROW}</div>')
        out.append(f'<div class="card step" style="{vars_(s.get("color"))}"><div class="num">STEP {i:02d}</div>'
                   f'{badge(s.get("icon"))}<div class="t">{esc(s["title"])}</div><div class="d">{esc(s.get("desc"))}</div></div>')
    return f'<div class="flow">{"".join(out)}</div>'


def cards(d, th):
    items = "".join(f'<div class="card" style="{vars_(c.get("color"))}">{badge(c.get("icon"))}'
                    f'<div class="t">{esc(c["title"])}</div><div class="d">{esc(c.get("desc"))}</div></div>'
                    for c in d["cards"])
    return f'<div class="grid" style="grid-template-columns:repeat({d.get("columns", 3)},1fr)">{items}</div>'


def compare(d, th):
    def panel(side, cls, mark):
        lis = "".join(f"<li><i>{mark}</i><span>{esc(x)}</span></li>" for x in side["items"])
        return f'<div class="panel {cls}"><h2>{esc(side["title"])}</h2><ul>{lis}</ul></div>'
    return (f'<div class="cmp">{panel(d["left"], "bad", "✕")}<div class="mid"><div class="conn">{ARROW}</div></div>'
            f'{panel(d["right"], "good", "✓")}</div>')


def matrix(d, th):
    x, y, c = d["x_axis"], d["y_axis"], d["cells"]

    def cell(k):
        return (f'<div class="card cell" style="{vars_(k.get("color"))}">{badge(k.get("icon"))}'
                f'<div class="t">{esc(k["title"])}</div><div class="d">{esc(k.get("desc"))}</div></div>')
    return (f'<div class="mx"><div></div><div class="ax">{esc(x[0])}</div><div class="ax">{esc(x[1])}</div>'
            f'<div class="ax">{esc(y[0])}</div>{cell(c[0])}{cell(c[1])}<div class="ax">{esc(y[1])}</div>{cell(c[2])}{cell(c[3])}</div>')


def spectrum(d, th):
    labels = f'<div class="spec-labels"><span>{esc(d.get("left_label"))}</span><span>{esc(d.get("right_label"))}</span></div>'
    return f'{labels}<div class="spec-bar"></div>' + cards({"cards": d["items"], "columns": len(d["items"])}, th)


def triple(d, th):
    rows = []
    for r in d["rows"]:
        s, p, o = r["s"], r["p"], r["o"]
        rows.append(f'<div class="row"><div class="node" style="{vars_(s.get("color"), "indigo")}">{esc(s["label"])}'
                    f'<small>{esc(s.get("type"))}</small></div><div class="edge"><span>{esc(p)}</span></div>'
                    f'<div class="node" style="{vars_(o.get("color"), "teal")}">{esc(o["label"])}<small>{esc(o.get("type"))}</small></div></div>')
    return f'<div class="trip">{"".join(rows)}</div>'


def stack(d, th):
    rows = "".join(f'<div class="layer" style="{vars_(l.get("color"))}">{badge(l.get("icon"))}'
                   f'<div class="t">{esc(l["title"])}</div><div class="d">{esc(l.get("desc"))}</div></div>'
                   for l in d["layers"])
    return f'<div class="stack">{rows}</div>'


LAYOUTS = {"flow": flow, "cards": cards, "compare": compare, "matrix": matrix,
           "spectrum": spectrum, "triple": triple, "stack": stack}


def title_html(t: str) -> str:
    # *강조* 표기를 그라데이션 강조로
    parts = esc(t).split("*")
    return "".join(f"<em>{p}</em>" if i % 2 else p for i, p in enumerate(parts))


def page(d: dict, th: dict) -> str:
    kicker = d.get("kicker") or th.get("book", "")
    sub = f'<div class="sub">{esc(d["subtitle"])}</div>' if d.get("subtitle") else ""
    note = (f'<div class="note"><span class="ic">💡</span><span>{esc(d["note"])}</span></div>' if d.get("note") else "")
    foot = f'<div class="foot"><span>{esc(th.get("book", ""))}</span><span>{esc(th.get("site", "wikidocs.net"))}</span></div>'
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css(th)}</style></head><body><div id="c"><div class="z">'
            f'<div class="kicker"><span class="dot"></span>{esc(kicker)}</div><h1>{title_html(d["title"])}</h1>{sub}'
            f'<div class="body">{LAYOUTS[d["layout"]](d, th)}</div>{note}{foot}</div></div></body></html>')


SHOT_JS = """
const { chromium } = require('playwright');
const jobs = JSON.parse(process.argv[2]);
(async () => {
  const browser = await chromium.launch();
  const page = await browser.newPage({ viewport: { width: 1200, height: 800 }, deviceScaleFactor: 2 });
  for (const j of jobs) {
    await page.goto('file://' + j.html);
    await page.evaluate(() => document.fonts.ready);
    await page.locator('#c').screenshot({ path: j.png });
    console.log('  ✓ ' + j.name);
  }
  await browser.close();
})();
"""


def main() -> None:
    only = sys.argv[1] if len(sys.argv) > 1 else ""
    data = yaml.safe_load((ROOT / "tools" / "diagrams.yaml").read_text(encoding="utf-8"))
    theme = data.get("theme", {})
    ASSETS.mkdir(exist_ok=True)
    jobs = []
    with tempfile.TemporaryDirectory() as tmp:
        for d in data["diagrams"]:
            if only and only not in d["file"]:
                continue
            if d["layout"] not in LAYOUTS:
                sys.exit(f"[오류] 알 수 없는 layout: {d['layout']} ({d['file']})")
            h = Path(tmp) / (Path(d["file"]).stem + ".html")
            h.write_text(page(d, theme), encoding="utf-8")
            jobs.append({"html": str(h), "png": str(ASSETS / d["file"]), "name": d["file"]})
        if not jobs:
            sys.exit("만들 이미지가 없습니다.")
        print(f"[이미지 생성] {len(jobs)}개")
        js = Path(tmp) / "shot.js"
        js.write_text(SHOT_JS, encoding="utf-8")
        subprocess.run(["node", str(js), json.dumps(jobs)], check=True, cwd=tmp)


if __name__ == "__main__":
    main()
