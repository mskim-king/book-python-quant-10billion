#!/usr/bin/env python3
"""책 표지(assets/cover.png, 1200x1600)를 만듭니다.

사용법:  python tools/build_cover.py
설정:    tools/cover.yaml (권 번호, 키워드, 아이콘, 색) + structure.yaml(제목·부제)
필요:    Python(pyyaml), Node.js + Playwright, Noto Sans CJK KR, Noto Color Emoji
"""
from __future__ import annotations

import html
import json
import subprocess
import tempfile
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
PAL = {  # 진한, 중간, 밝은 강조
    "indigo": ("#1E1B4B", "#4338CA", "#A5B4FC"), "cyan": ("#083344", "#0891B2", "#67E8F9"),
    "teal": ("#042F2E", "#0F766E", "#5EEAD4"), "blue": ("#172554", "#1D4ED8", "#93C5FD"),
    "emerald": ("#022C22", "#047857", "#6EE7B7"), "violet": ("#2E1065", "#6D28D9", "#C4B5FD"),
    "pink": ("#500724", "#BE185D", "#F9A8D4"), "amber": ("#451A03", "#B45309", "#FCD34D"),
}


def esc(s) -> str:
    return html.escape(str(s or ""))


def page(book: dict, cov: dict) -> str:
    p1, p2, p3 = PAL[cov.get("primary", "indigo")]
    s1, s2, s3 = PAL[cov.get("secondary", "cyan")]
    # cover.yaml 의 title: '|' 는 줄바꿈, *강조* 는 그라데이션 강조
    parts = esc(cov.get("title") or book["title"]).split("*")
    title = "".join(f"<em>{x}</em>" if i % 2 else x for i, x in enumerate(parts)).replace("|", "<br>")
    icons = "".join(f'<div class="ic" style="--d:{i*0.0}s"><span>{esc(x)}</span></div>' for i, x in enumerate(cov["icons"]))
    chips = "".join(f"<span>{esc(k)}</span>" for k in cov["keywords"])
    # 장식용 연결선(네트워크) — 노드 좌표 고정
    nodes = [(140, 120), (420, 60), (700, 170), (980, 80), (260, 330), (600, 380), (900, 330)]
    edges = [(0, 1), (1, 2), (2, 3), (0, 4), (4, 5), (5, 6), (2, 5), (3, 6), (1, 4)]
    svg = "".join(f'<line x1="{nodes[a][0]}" y1="{nodes[a][1]}" x2="{nodes[b][0]}" y2="{nodes[b][1]}"/>' for a, b in edges)
    svg += "".join(f'<circle cx="{x}" cy="{y}" r="{10 if i % 2 else 16}"/>' for i, (x, y) in enumerate(nodes))
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
* {{ margin:0; padding:0; box-sizing:border-box; }}
body {{ font-family:'Noto Sans CJK KR',sans-serif; }}
#c {{ width:1200px; height:1600px; position:relative; overflow:hidden; color:#fff;
  background: radial-gradient(circle at 85% 12%, {s2}cc 0%, transparent 42%),
              radial-gradient(circle at 10% 90%, {p2}dd 0%, transparent 50%),
              linear-gradient(160deg, {p1} 0%, {p2} 55%, {s1} 100%); }}
#c::before {{ content:''; position:absolute; inset:0; opacity:.13;
  background-image: linear-gradient(#fff 1px, transparent 1px), linear-gradient(90deg, #fff 1px, transparent 1px);
  background-size: 60px 60px; mask-image: linear-gradient(180deg, #000 0%, transparent 70%); }}
.wrap {{ position:absolute; inset:0; padding:96px 96px 80px; display:flex; flex-direction:column; }}
.series {{ display:inline-flex; align-self:flex-start; align-items:center; gap:14px; padding:14px 26px; border-radius:999px;
  background:rgba(255,255,255,.12); border:1px solid rgba(255,255,255,.28); font-size:26px; font-weight:700; letter-spacing:1px; }}
.series b {{ color:{s3}; }}
.net {{ margin-top:70px; height:440px; position:relative; }}
.net svg {{ position:absolute; inset:0; width:100%; height:100%; }}
.net line {{ stroke:{s3}; stroke-opacity:.45; stroke-width:3; }}
.net circle {{ fill:{s3}; fill-opacity:.85; }}
.icons {{ position:absolute; left:0; right:0; top:120px; display:flex; justify-content:center; gap:44px; }}
.ic {{ width:200px; height:200px; border-radius:56px; display:flex; align-items:center; justify-content:center;
  background:linear-gradient(140deg, rgba(255,255,255,.28), rgba(255,255,255,.06)); border:1.5px solid rgba(255,255,255,.4);
  box-shadow:0 30px 60px -20px rgba(0,0,0,.55), inset 0 1px 0 rgba(255,255,255,.4); backdrop-filter: blur(6px); }}
.ic span {{ font-family:'Noto Color Emoji'; font-size:104px; filter:drop-shadow(0 8px 10px rgba(0,0,0,.35)); }}
.ic:nth-child(2) {{ transform:translateY(-40px) scale(1.12); }}
h1 {{ margin-top:60px; font-size:{cov.get('title_size', 112)}px; font-weight:800; line-height:1.15; letter-spacing:-3px;
  text-shadow:0 6px 30px rgba(0,0,0,.35); }}
h1 em {{ font-style:normal; background:linear-gradient(90deg,#fff, {s3}); -webkit-background-clip:text; color:transparent; }}
.sub {{ margin-top:30px; font-size:40px; font-weight:500; color:rgba(255,255,255,.88); line-height:1.4; }}
.bar {{ margin-top:44px; width:120px; height:8px; border-radius:8px; background:linear-gradient(90deg,{s3},{p3}); }}
.chips {{ margin-top:auto; display:flex; flex-wrap:wrap; gap:16px; }}
.chips span {{ padding:14px 26px; border-radius:16px; font-size:28px; font-weight:700; background:rgba(0,0,0,.22);
  border:1px solid rgba(255,255,255,.22); }}
.foot {{ margin-top:40px; display:flex; justify-content:space-between; align-items:flex-end; font-size:26px; color:rgba(255,255,255,.75); }}
.foot b {{ font-size:30px; color:#fff; letter-spacing:1px; }}
</style></head><body><div id="c"><div class="wrap">
<div class="series">AI 시대 데이터 실무 4부작 · <b>VOL.{cov['vol']}</b></div>
<div class="net"><svg viewBox="0 0 1008 440">{svg}</svg><div class="icons">{icons}</div></div>
<h1>{title}</h1>
<div class="sub">{esc(book.get('subtitle'))}</div>
<div class="bar"></div>
<div class="chips">{chips}</div>
<div class="foot"><span>{esc(cov.get('author', ''))}</span><b>wikidocs</b></div>
</div></div></body></html>"""


SHOT = """
const { chromium } = require('playwright');
(async () => {
  const [html, png] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
  await p.goto('file://' + html); await p.evaluate(() => document.fonts.ready);
  await p.locator('#c').screenshot({ path: png }); await b.close();
})();
"""


def main() -> None:
    book = yaml.safe_load((ROOT / "structure.yaml").read_text(encoding="utf-8"))["book"]
    cov = yaml.safe_load((ROOT / "tools" / "cover.yaml").read_text(encoding="utf-8"))
    out = ROOT / "assets" / "cover.png"
    out.parent.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory() as tmp:
        h = Path(tmp) / "cover.html"
        h.write_text(page(book, cov), encoding="utf-8")
        js = Path(tmp) / "shot.js"
        js.write_text(SHOT, encoding="utf-8")
        subprocess.run(["node", str(js), str(h), str(out)], check=True, cwd=tmp)
    print(f"[표지] {out.relative_to(ROOT)} (1200x1600)")


if __name__ == "__main__":
    main()
