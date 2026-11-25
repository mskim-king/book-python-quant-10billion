#!/usr/bin/env python3
"""책 표지(assets/cover.png, 1200x1600)를 만듭니다.

사용법:  python tools/build_cover.py
설정:    tools/cover.yaml (권 번호, 키워드, 아이콘, 색) + structure.yaml(제목·부제)
         style: fun 이면 만화풍 표지(hook·hero·bubble·burst·stickers 사용, 글꼴 Jua·Gaegu)
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


FONTS = ROOT / "tools" / "vendor" / "fonts"
TILT = [-6, 4, -3, 5, -4, 3]


def page_fun(book: dict, cov: dict) -> str:
    p1, p2, p3 = PAL[cov.get("primary", "indigo")]
    s1, s2, s3 = PAL[cov.get("secondary", "cyan")]
    bg = cov.get("bg", "#FFF4D6")
    f = lambda n: (FONTS / n).as_uri()
    parts = esc(cov.get("title") or book["title"]).split("*")
    title = "".join(f"<em>{x}</em>" if i % 2 else x for i, x in enumerate(parts)).replace("|", "<br>")
    chip_bg = [s3, "#FDE68A", p3, "#FBCFE8", "#BBF7D0", "#BAE6FD"]
    chips = "".join(f'<span style="background:{chip_bg[i % 6]};transform:rotate({TILT[i % 6] * .6}deg)">{esc(k)}</span>'
                    for i, k in enumerate(cov["keywords"]))
    pos = [(60, 40, -14), (880, 10, 12), (990, 170, -8), (20, 330, 10)]
    stickers = "".join(f'<i style="left:{x}px;top:{y}px;transform:rotate({r}deg)">{esc(e)}</i>'
                       for e, (x, y, r) in zip(cov.get("stickers", cov["icons"]), pos))
    bubble = esc(cov.get("bubble", "")).replace("|", "<br>")
    note = f'<div class="note">{esc(cov["note"])}</div>' if cov.get("note") else ""
    doodle = ("data:image/svg+xml;utf8,<svg xmlns='http://www.w3.org/2000/svg' width='180' height='180'>"
              "<g fill='none' stroke='%23000' stroke-opacity='.08' stroke-width='4' stroke-linecap='round'>"
              "<path d='M24 34 l7 -14 l7 14 l-14 -8 h14 z'/><circle cx='135' cy='45' r='9'/>"
              "<path d='M40 135 q12 -16 24 0 t24 0'/><path d='M140 128 l12 12 m0 -12 l-12 12'/></g></svg>")
    return f"""<!doctype html><html><head><meta charset="utf-8"><style>
@font-face {{ font-family:'JuaL'; src:url({f('jua-latin-400-normal.woff2')}); }}
@font-face {{ font-family:'Jua'; src:url({f('jua-korean-400-normal.woff2')}); }}
@font-face {{ font-family:'GaeguL'; font-weight:700; src:url({f('gaegu-latin-700-normal.woff2')}); }}
@font-face {{ font-family:'Gaegu'; font-weight:700; src:url({f('gaegu-korean-700-normal.woff2')}); }}
* {{ margin:0; padding:0; box-sizing:border-box; }}
#c {{ width:1200px; height:1600px; position:relative; overflow:hidden; color:#1E1B3A;
  font-family:'JuaL','Jua','Noto Color Emoji',sans-serif; background:{bg} url("{doodle}"); word-break:keep-all; }}
#c::before {{ content:''; position:absolute; left:0; right:0; top:0; height:34px;
  background:repeating-linear-gradient(-45deg,{p2} 0 34px,#FACC15 34px 68px,{s2} 68px 102px); }}
#c::after {{ content:''; position:absolute; right:-160px; bottom:-160px; width:620px; height:620px; border-radius:50%;
  background:radial-gradient({s3} 3px, transparent 4px) 0 0/26px 26px; opacity:.7; }}
.wrap {{ position:absolute; inset:0; padding:92px 84px 70px; display:flex; flex-direction:column; z-index:1; }}
.top {{ display:flex; justify-content:space-between; align-items:center; }}
.series {{ background:#fff; border:5px solid #1E1B3A; border-radius:999px; padding:12px 30px; font-size:32px;
  box-shadow:7px 7px 0 #1E1B3A; transform:rotate(-2deg); }}
.vol {{ width:170px; height:170px; border-radius:50%; background:#FACC15; border:6px solid #1E1B3A; box-shadow:8px 8px 0 #1E1B3A;
  display:flex; flex-direction:column; align-items:center; justify-content:center; transform:rotate(10deg); line-height:1; }}
.vol small {{ font-size:30px; }} .vol b {{ font-size:84px; font-weight:400; }}
.deco {{ position:absolute; right:70px; top:{cov.get('deco_top', 330)}px; font-family:'Noto Color Emoji'; font-size:270px; line-height:1;
  transform:rotate(14deg); filter:drop-shadow(10px 12px 0 rgba(30,27,58,.18)); z-index:0; }}
.hook {{ margin-top:34px; font-family:'GaeguL','Gaegu'; font-weight:700; font-size:50px; letter-spacing:-0.06em; color:{p2};
  transform:rotate(-1.5deg); }}
h1 {{ margin-top:6px; font-weight:400; font-size:{cov.get('title_size', 112) + 18}px; line-height:1.12; letter-spacing:-2px;
  -webkit-text-stroke:0; text-shadow:6px 6px 0 #fff, -2px -2px 0 #fff, 2px -2px 0 #fff, -2px 2px 0 #fff; }}
h1 em {{ font-style:normal; color:{p2}; background:linear-gradient(transparent 58%, {s3} 58%, {s3} 92%, transparent 92%); padding:0 6px; }}
.sub {{ margin-top:18px; font-family:'GaeguL','Gaegu'; font-weight:700; font-size:46px; letter-spacing:-0.07em; }}
.scene {{ position:relative; margin-top:44px; height:500px; }}
.card {{ position:absolute; left:60px; right:60px; top:60px; bottom:30px; background:#fff; border:6px solid #1E1B3A; border-radius:48px;
  box-shadow:14px 14px 0 #1E1B3A; transform:rotate(-1.5deg); display:flex; align-items:center; padding:0 50px; gap:30px; }}
.hero {{ font-family:'Noto Color Emoji'; font-size:230px; line-height:1; filter:drop-shadow(0 10px 0 rgba(0,0,0,.12)); }}
.bubble {{ position:relative; flex:1; background:{bg}; border:5px solid #1E1B3A; border-radius:40px; padding:34px 36px;
  font-size:52px; line-height:1.3; }}
.bubble::before {{ content:''; position:absolute; left:-34px; top:50%; margin-top:-22px; border:22px solid transparent;
  border-right:30px solid #1E1B3A; border-left:0; }}
.bubble::after {{ content:''; position:absolute; left:-24px; top:50%; margin-top:-16px; border:16px solid transparent;
  border-right:22px solid {bg}; border-left:0; }}
.scene i {{ position:absolute; font-style:normal; font-family:'Noto Color Emoji'; font-size:120px; z-index:2;
  filter:drop-shadow(5px 6px 0 rgba(30,27,58,.25)); }}
.burst {{ position:absolute; right:-10px; bottom:-34px; z-index:3; width:250px; height:250px; display:flex; align-items:center;
  justify-content:center; text-align:center; font-size:38px; line-height:1.15; color:#fff; padding:40px;
  background:#EF4444; transform:rotate(12deg);
  clip-path:polygon(50% 0,61% 13%,77% 6%,80% 22%,96% 24%,89% 39%,100% 50%,89% 61%,96% 76%,80% 78%,77% 94%,61% 87%,50% 100%,39% 87%,23% 94%,20% 78%,4% 76%,11% 61%,0 50%,11% 39%,4% 24%,20% 22%,23% 6%,39% 13%); }}
.chips {{ margin-top:auto; display:flex; flex-wrap:wrap; gap:18px; }}
.chips span {{ border:4px solid #1E1B3A; border-radius:18px; padding:12px 26px; font-size:36px; box-shadow:5px 5px 0 #1E1B3A; }}
.foot {{ margin-top:34px; display:flex; justify-content:space-between; align-items:center; font-size:32px; }}
.note {{ font-family:'GaeguL','Gaegu'; font-weight:700; font-size:32px; color:#57534E; }}
.foot b {{ font-weight:400; background:#1E1B3A; color:#fff; padding:8px 24px; border-radius:14px; }}
</style></head><body><div id="c"><div class="wrap">
<div class="top"><div class="series">📚 AI 시대 데이터 실무 4부작</div><div class="vol"><small>VOL.</small><b>{cov['vol']}</b></div></div>
<div class="deco">{esc(cov.get('deco', ''))}</div>
<div class="hook">{esc(cov.get('hook', ''))}</div>
<h1>{title}</h1>
<div class="sub">{esc(book.get('subtitle'))}</div>
<div class="scene">{stickers}<div class="card"><div class="hero">{esc(cov.get('hero', cov['icons'][0]))}</div>
<div class="bubble">{bubble}</div></div><div class="burst">{esc(cov.get('burst', '')).replace('|', '<br>')}</div></div>
<div class="chips">{chips}</div>
<div class="foot">{note or '<span></span>'}<b>wikidocs</b></div>
</div></div></body></html>"""


SHOT = """
const { chromium } = require('playwright');
(async () => {
  const [html, png] = process.argv.slice(2);
  const b = await chromium.launch();
  const p = await b.newPage({ viewport: { width: 1200, height: 1600 }, deviceScaleFactor: 1 });
  await p.goto('file://' + html); await p.evaluate(() => document.fonts.ready); await p.waitForTimeout(300);
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
        h.write_text((page_fun if cov.get("style") == "fun" else page)(book, cov), encoding="utf-8")
        js = Path(tmp) / "shot.js"
        js.write_text(SHOT, encoding="utf-8")
        subprocess.run(["node", str(js), str(h), str(out)], check=True, cwd=tmp)
    print(f"[표지] {out.relative_to(ROOT)} (1200x1600)")


if __name__ == "__main__":
    main()
