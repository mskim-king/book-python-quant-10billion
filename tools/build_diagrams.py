#!/usr/bin/env python3
"""tools/diagrams.yaml 에 정의한 설명 이미지를 assets/*.png 로 만듭니다. (디자인 v3)

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
    공통 선택 항목: 카드·단계·칸·층에 ex: "예시 문장" 을 넣으면 아래에 예시 상자가 붙습니다.
                    mark: 오른쪽 위 큰 배경 번호 (없으면 파일 이름에서 장 번호를 씁니다)
    compare  tone: neutral 이면 두 표현을 VS 로 비교
    chart    데이터 그래프 kind: bar|hbar|line|radar|scatter (categories, series, indicators, points, quadrants)
    network  관계도 (nodes: [{name, group, x, y, size, shape}], groups, links: [[a, b, 라벨]], arrows)
    sankey   흐름도 (nodes: [{name, color}], links: [[a, b, 값]])
    timeline 타임라인 (events: [{date, title, desc, color, ex}])
    bars     순위 막대 그래프 (groups: [{title, min, max, items: [{label, sub, value, color, tag}]}])

필요한 것: Python(pyyaml), Node.js + Playwright, 한글 글꼴(Noto Sans CJK KR), 이모지 글꼴(Noto Color Emoji)
"""
from __future__ import annotations

import html
import json
import re
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
body {{ background: #fff; word-break: keep-all; font-family: 'Noto Sans CJK KR', sans-serif; color: #0F172A; -webkit-font-smoothing: antialiased; }}
#c {{ width: 1200px; padding: 52px 56px 34px; position: relative; overflow: hidden; background: #FFFFFF;
  background-image: radial-gradient(#E2E8F0 1.2px, transparent 1.2px); background-size: 22px 22px; }}
#c .topbar {{ position: absolute; left: 0; right: 0; top: 0; height: 10px; background: linear-gradient(90deg, {p1}, {p2}, {s2}); z-index: 2; }}
#c .mark {{ position: absolute; right: 40px; top: 18px; font-size: 150px; font-weight: 900; letter-spacing: -6px; line-height: 1;
  color: transparent; -webkit-text-stroke: 2px {p2}2e; z-index: 0; }}
#c::before {{ content: ''; position: absolute; width: 620px; height: 620px; right: -220px; top: -330px;
  background: radial-gradient(circle, {p2}33 0%, transparent 65%); }}
#c::after {{ content: ''; position: absolute; width: 520px; height: 520px; left: -260px; bottom: -320px;
  background: radial-gradient(circle, {s2}26 0%, transparent 65%); }}
.z {{ position: relative; z-index: 1; }}
.kicker {{ display: inline-flex; align-items: center; gap: 10px; font-size: 16px; font-weight: 700; letter-spacing: 1.5px;
  color: {p1}; background: {p3}; border: 1px solid {p2}40; padding: 7px 14px; border-radius: 999px; }}
.kicker .dot {{ width: 8px; height: 8px; border-radius: 50%; background: linear-gradient(135deg, {p2}, {s2}); }}
h1 {{ margin-top: 16px; font-size: 46px; font-weight: 800; letter-spacing: -1px; line-height: 1.25; }}
h1 em {{ font-style: normal; background: linear-gradient(90deg, {p1}, {s1}); -webkit-background-clip: text; color: transparent; }}
.sub {{ margin-top: 10px; font-size: 23px; color: #475569; line-height: 1.5; }}
.body {{ margin-top: 34px; }}
.badge {{ width: 76px; height: 76px; border-radius: 24px; border: 4px solid #fff; outline: 2px solid var(--l); display: flex; align-items: center; justify-content: center;
  font-size: 36px; font-family: 'Noto Color Emoji', sans-serif; background: linear-gradient(135deg, var(--m), var(--d));
  box-shadow: 0 10px 20px -8px var(--m); }}
.badge span {{ filter: drop-shadow(0 2px 2px rgba(0,0,0,.15)); }}
.t {{ font-size: 25px; font-weight: 800; letter-spacing: -0.3px; color: var(--d); }}
.d {{ font-size: 19px; color: #334155; line-height: 1.55; white-space: pre-line; }}
.card {{ background: #fff; border-radius: 24px; padding: 28px 24px 24px; border: 1px solid #E2E8F0;
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
.panel li {{ list-style: none; font-size: 20px; line-height: 1.5; padding: 13px 16px; margin-top: 10px; border-radius: 12px;
  display: flex; gap: 12px; align-items: flex-start; }}
.panel li i {{ font-style: normal; font-weight: 800; flex: none; width: 24px; height: 24px; border-radius: 50%; color: #fff;
  font-size: 14px; display: flex; align-items: center; justify-content: center; margin-top: 3px; }}
.bad h2 {{ background: linear-gradient(90deg, #DC2626, #F43F5E); }} .bad li {{ background: #FEF2F2; }} .bad li i {{ background: #EF4444; }}
.good h2 {{ background: linear-gradient(90deg, #059669, #10B981); }} .good li {{ background: #ECFDF5; }} .good li i {{ background: #10B981; }}
.mid {{ display: flex; align-items: center; justify-content: center; }}
.neu1 h2 {{ background: linear-gradient(90deg, {p1}, {p2}); }} .neu1 li {{ background: {p3}; }} .neu1 li i {{ background: {p2}; }}
.neu2 h2 {{ background: linear-gradient(90deg, {s1}, {s2}); }} .neu2 li {{ background: #F8FAFC; }} .neu2 li i {{ background: {s2}; }}
.vs {{ width: 52px; height: 52px; border-radius: 50%; display: flex; align-items: center; justify-content: center;
  font-size: 16px; font-weight: 800; color: #fff; background: linear-gradient(135deg, {p2}, {s2}); box-shadow: 0 8px 18px -8px {p2}; }}
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
.node {{ border-radius: 999px; padding: 16px 22px; text-align: center; font-size: 22px; font-weight: 800; color: var(--d);
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
.note {{ margin-top: 30px; padding: 18px 24px 18px 20px; border-radius: 18px; display: flex; gap: 16px; align-items: center;
  background: linear-gradient(90deg, {p3}, #FFFFFF); border: 1px solid {p2}40; border-left: 8px solid {p2};
  color: #0F172A; font-size: 21px; font-weight: 700; box-shadow: 0 12px 26px -18px {p2}; }}
.note .ic {{ font-family: 'Noto Color Emoji'; font-size: 24px; width: 46px; height: 46px; flex: none; border-radius: 14px;
  display: flex; align-items: center; justify-content: center; background: #fff; box-shadow: 0 4px 10px -4px {p2}80; }}
/* example box */
.ex {{ margin-top: 14px; text-align: left; font-size: 16.5px; line-height: 1.5; color: #1E293B; background: var(--l);
  border-radius: 12px; padding: 10px 12px; border: 1px dashed var(--m); white-space: pre-line; }}
.ex b {{ display: inline-block; font-size: 13px; font-weight: 800; color: #fff; background: var(--m); border-radius: 6px;
  padding: 1px 7px; margin-right: 6px; vertical-align: 1px; }}
.layer .ex {{ grid-column: 3; margin-top: 6px; }}
.foot {{ margin-top: 22px; display: flex; justify-content: space-between; font-size: 14px; color: #94A3B8; font-weight: 600; letter-spacing: .5px; }}
"""


def vars_(color: str | None, default: str = "indigo") -> str:
    d, m, l = pal(color, default)
    return f"--d:{d};--m:{m};--l:{l}"


def ex(item) -> str:
    return f'<div class="ex"><b>예</b>{esc(item["ex"])}</div>' if item.get("ex") else ""


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
                   f'{badge(s.get("icon"))}<div class="t">{esc(s["title"])}</div><div class="d">{esc(s.get("desc"))}</div>{ex(s)}</div>')
    return f'<div class="flow">{"".join(out)}</div>'


def cards(d, th):
    items = "".join(f'<div class="card" style="{vars_(c.get("color"))}">{badge(c.get("icon"))}'
                    f'<div class="t">{esc(c["title"])}</div><div class="d">{esc(c.get("desc"))}</div>{ex(c)}</div>'
                    for c in d["cards"])
    return f'<div class="grid" style="grid-template-columns:repeat({d.get("columns", 3)},1fr)">{items}</div>'


def compare(d, th):
    def panel(side, cls, mark):
        lis = "".join(f"<li><i>{mark}</i><span>{esc(x)}</span></li>" for x in side["items"])
        return f'<div class="panel {cls}"><h2>{esc(side["title"])}</h2><ul>{lis}</ul></div>'
    if d.get("tone") == "neutral":
        left, right = panel(d["left"], "neu1", "•"), panel(d["right"], "neu2", "•")
    else:
        left, right = panel(d["left"], "bad", "✕"), panel(d["right"], "good", "✓")
    mid = (f'<div class="conn">{ARROW}</div>' if d.get("tone") != "neutral" or d.get("arrow")
           else '<div class="vs">VS</div>')
    return f'<div class="cmp">{left}<div class="mid">{mid}</div>{right}</div>'


def matrix(d, th):
    x, y, c = d["x_axis"], d["y_axis"], d["cells"]

    def cell(k):
        return (f'<div class="card cell" style="{vars_(k.get("color"))}">{badge(k.get("icon"))}'
                f'<div class="t">{esc(k["title"])}</div><div class="d">{esc(k.get("desc"))}</div>{ex(k)}</div>')
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
                   f'<div class="t">{esc(l["title"])}</div><div class="d">{esc(l.get("desc"))}</div>{ex(l)}</div>'
                   for l in d["layers"])
    return f'<div class="stack">{rows}</div>'


BARS_CSS = """
.bars { display: grid; gap: 22px; }
.bgrp { background: #fff; border: 1px solid #E2E8F0; border-radius: 22px; padding: 22px 24px 18px;
  box-shadow: 0 10px 30px -18px rgba(15,23,42,.25); }
.bgrp h2 { font-size: 21px; font-weight: 800; margin-bottom: 4px; }
.bgrp .bs { font-size: 13.5px; color: #64748B; margin-bottom: 14px; }
.brow { display: grid; grid-template-columns: 34px 190px 1fr 104px; align-items: center; gap: 10px; margin: 9px 0; }
.brk { width: 30px; height: 30px; border-radius: 9px; display: grid; place-items: center; font-weight: 800;
  font-size: 15px; color: #fff; background: var(--m); }
.blb { font-size: 15.5px; font-weight: 700; line-height: 1.2; }
.blb small { display: block; font-size: 12px; font-weight: 500; color: #64748B; }
.btrack { position: relative; height: 30px; background: #F1F5F9; border-radius: 9px; }
.bfill { position: absolute; left: 0; top: 0; bottom: 0; border-radius: 9px;
  background: linear-gradient(90deg, var(--l), var(--m)); }
.bval { display: flex; align-items: center; justify-content: flex-end; gap: 6px;
  font-size: 15px; font-weight: 800; color: var(--d); }
.btag { font-size: 11px; font-weight: 700; padding: 2px 7px; border-radius: 6px; background: #fff; border: 1px solid var(--m); color: var(--d); }
"""


def bars(d, th):
    out = []
    for g in d["groups"]:
        lo, hi = g.get("min", 0), g.get("max", 100)
        rows = []
        for i, it in enumerate(g["items"], 1):
            w = max(4, min(100, (float(it["value"]) - lo) / (hi - lo) * 100))
            tag = f'<span class="btag">{esc(it["tag"])}</span>' if it.get("tag") else ""
            rows.append(f'<div class="brow" style="{vars_(it.get("color"))}"><div class="brk">{esc(it.get("rank", i))}</div>'
                        f'<div class="blb">{esc(it["label"])}<small>{esc(it.get("sub"))}</small></div>'
                        f'<div class="btrack"><div class="bfill" style="width:{w:.1f}%"></div></div>'
                        f'<div class="bval">{tag}{esc(it.get("display", it["value"]))}</div></div>')
        bs = f'<div class="bs">{esc(g["subtitle"])}</div>' if g.get("subtitle") else ""
        out.append(f'<div class="bgrp"><h2>{esc(g["title"])}</h2>{bs}{"".join(rows)}</div>')
    cols = d.get("columns", len(d["groups"]))
    return f'<style>{BARS_CSS}</style><div class="bars" style="grid-template-columns:repeat({cols},1fr)">{"".join(out)}</div>'


# ---------- 데이터 시각화 레이아웃 (ECharts, tools/vendor 에 포함) ----------
ECHARTS = ROOT / "tools" / "vendor" / "echarts-5.5.1.min.js"
VIZ_CSS = """
.viz { background: #fff; border: 1px solid #E2E8F0; border-radius: 24px; padding: 14px 12px 8px;
  box-shadow: 0 1px 2px rgba(15,23,42,.04), 0 12px 28px -14px rgba(15,23,42,.2); }
.viz .src { font-size: 13.5px; color: #64748B; padding: 2px 14px 6px; }
.legend { display: flex; flex-wrap: wrap; gap: 10px 22px; padding: 4px 14px 10px; font-size: 16px; font-weight: 700; color: #334155; }
.legend i { display: inline-block; width: 16px; height: 16px; border-radius: 5px; margin-right: 7px; vertical-align: -2px; }
.tl { position: relative; display: grid; gap: 16px; padding-top: 34px; }
.tl::before { content: ''; position: absolute; left: 0; right: 0; top: 46px; height: 6px; border-radius: 3px;
  background: linear-gradient(90deg, var(--p2), var(--s2)); }
.tl .ev { position: relative; text-align: center; }
.tl .dt { position: absolute; top: -34px; left: 0; right: 0; font-size: 15px; font-weight: 800; color: #475569; }
.tl .pin { width: 30px; height: 30px; border-radius: 50%; margin: 0 auto; background: #fff; border: 7px solid var(--m);
  box-shadow: 0 6px 14px -6px var(--m); position: relative; z-index: 1; }
.tl .card { margin-top: 16px; padding: 18px 14px 16px; text-align: center; }
.tl .card .t { margin-top: 0; font-size: 21px; } .tl .card .d { font-size: 16.5px; }
"""
_viz_n = [0]


def _col(name, default="indigo"):
    return pal(name, default)[1]


def _echart(opt: dict, height: int, legend: str = "", src: str = "") -> str:
    _viz_n[0] += 1
    cid = f"vz{_viz_n[0]}"
    s = f'<div class="src">{esc(src)}</div>' if src else ""
    return (f'<style>{VIZ_CSS}</style><div class="viz"><div id="{cid}" style="width:100%;height:{height}px"></div>{legend}{s}</div>'
            f'<script>(function(){{var c=echarts.init(document.getElementById("{cid}"),null,{{renderer:"svg"}});'
            f'var o={json.dumps(opt, ensure_ascii=False)};o.animation=false;'
            f'o.textStyle={{fontFamily:"Noto Sans CJK KR",color:"#0F172A"}};c.setOption(o);}})();</script>')


def _legend(items) -> str:
    return '<div class="legend">' + "".join(f'<span><i style="background:{c}"></i>{esc(n)}</span>' for n, c in items) + "</div>"


AX = {"axisLabel": {"fontSize": 15, "color": "#334155"}, "axisLine": {"lineStyle": {"color": "#CBD5E1"}},
      "splitLine": {"lineStyle": {"color": "#EEF2F7"}}, "nameTextStyle": {"fontSize": 15, "color": "#64748B", "fontWeight": "bold"}}


def chart(d, th):
    """kind: bar | hbar | line | radar | scatter"""
    kind = d.get("kind", "bar")
    unit = d.get("unit", "")
    h = d.get("height", 440)
    series = d.get("series", [])
    leg = _legend([(x["name"], _col(x.get("color"))) for x in series]) if len(series) > 1 else ""
    opt = {"grid": {"left": 30, "right": 50, "top": 40 if len(series) < 2 else 30, "bottom": 20, "containLabel": True}}
    if kind in ("bar", "hbar", "line"):
        cat = {"type": "category", "data": d["categories"], **AX, "axisTick": {"show": False},
               "axisLabel": {"fontSize": 20 if kind == "hbar" else 17, "fontWeight": "bold", "color": "#0F172A", "interval": 0}}
        val = {"type": "value", **AX, "name": d.get("value_label", ""),
               "axisLabel": {"fontSize": 14, "color": "#64748B", "formatter": "{value}" + unit}}
        if d.get("max") is not None: val["max"] = d["max"]
        if d.get("min") is not None: val["min"] = d["min"]
        if kind == "hbar":
            cat["inverse"] = True
            opt["xAxis"], opt["yAxis"] = val, cat
        else:
            opt["xAxis"], opt["yAxis"] = cat, val
        out = []
        hi = d.get("highlight")
        for x in series:
            c = _col(x.get("color"))
            data = []
            for i, v in enumerate(x["data"]):
                item = {"value": v}
                if kind != "line" and hi is not None and len(series) == 1:
                    item["itemStyle"] = {"color": c if i == hi else "#CBD5E1"}
                data.append(item)
            sr = {"type": "line" if kind == "line" else "bar", "name": x["name"], "data": data,
                  "label": {"show": d.get("labels", True), "position": "right" if kind == "hbar" else "top",
                            "fontSize": 18, "fontWeight": "bold", "formatter": "{c}" + unit, "color": "#0F172A"}}
            if kind == "line":
                sr.update({"smooth": True, "symbolSize": 11, "lineStyle": {"width": 4, "color": c},
                           "itemStyle": {"color": c, "borderColor": "#fff", "borderWidth": 3},
                           "areaStyle": {"color": c, "opacity": 0.10} if len(series) == 1 else None})
            else:
                rad = [0, 10, 10, 0] if kind == "hbar" else [10, 10, 0, 0]
                sr.update({"barMaxWidth": 46, "itemStyle": {"color": c, "borderRadius": rad}})
                if hi is not None and len(series) == 1:
                    sr["data"] = [{**it, "itemStyle": {**it.get("itemStyle", {}), "borderRadius": rad}} for it in data]
            if x.get("mark"):
                m = x["mark"]
                coord = [m["at"], m["value"]] if kind != "hbar" else [m["value"], m["at"]]
                sr["markPoint"] = {"symbolSize": 64, "data": [{"coord": coord, "value": m["text"]}],
                                   "itemStyle": {"color": _col(m.get("color", "orange"))}, "label": {"fontSize": 14, "fontWeight": "bold"}}
            out.append(sr)
        opt["series"] = out
    elif kind == "radar":
        opt.pop("grid")
        opt["radar"] = {"indicator": [{"name": n, "max": d.get("max", 5)} for n in d["indicators"]], "radius": "74%",
                        "axisName": {"fontSize": 19, "fontWeight": "bold", "color": "#0F172A"},
                        "splitArea": {"areaStyle": {"color": ["#F8FAFC", "#FFFFFF"]}},
                        "splitLine": {"lineStyle": {"color": "#E2E8F0"}}, "axisLine": {"lineStyle": {"color": "#E2E8F0"}}}
        opt["series"] = [{"type": "radar", "symbolSize": 8, "data": [
            {"name": x["name"], "value": x["data"], "lineStyle": {"width": 3, "color": _col(x.get("color"))},
             "itemStyle": {"color": _col(x.get("color"))}, "areaStyle": {"color": _col(x.get("color")), "opacity": 0.14}}
            for x in series]}]
    elif kind == "scatter":
        xr, yr = d.get("x_range", [0, 10]), d.get("y_range", [0, 10])
        xm, ym = d.get("x_mid", sum(xr) / 2), d.get("y_mid", sum(yr) / 2)
        opt["grid"] = {"left": 70, "right": 40, "top": 30, "bottom": 60}
        opt["xAxis"] = {"type": "value", "min": xr[0], "max": xr[1], "name": d.get("x_label", ""), "nameLocation": "middle",
                        "nameGap": 34, **AX, "axisLabel": {"show": d.get("show_ticks", False)}, "splitLine": {"show": False}}
        opt["yAxis"] = {"type": "value", "min": yr[0], "max": yr[1], "name": d.get("y_label", ""), "nameLocation": "middle",
                        "nameGap": 40, **AX, "axisLabel": {"show": d.get("show_ticks", False)}, "splitLine": {"show": False}}
        pts = d["points"]
        q = d.get("quadrants")  # [좌상, 우상, 좌하, 우하]
        mark_area = []
        if q:
            qc = d.get("quadrant_colors", ["#ECFDF5", "#FFF7ED", "#FFF7ED", "#FEF2F2"])
            boxes = [([xr[0], ym], [xm, yr[1]]), ([xm, ym], [xr[1], yr[1]]), ([xr[0], yr[0]], [xm, ym]), ([xm, yr[0]], [xr[1], ym])]
            for (a, b), lab, col in zip(boxes, q, qc):
                mark_area.append([{"coord": a, "name": lab, "itemStyle": {"color": col}}, {"coord": b}])
        opt["series"] = [{"type": "scatter", "data": [
            {"name": p_["name"], "value": [p_["x"], p_["y"]], "symbolSize": p_.get("size", 26),
             **({"label": {"position": p_["label"]}} if p_.get("label") else {}),
             "itemStyle": {"color": _col(p_.get("color")), "borderColor": "#fff", "borderWidth": 3,
                           "shadowBlur": 10, "shadowColor": _col(p_.get("color"))}} for p_ in pts],
            "label": {"show": True, "formatter": "{b}", "position": "right", "fontSize": 17, "fontWeight": "bold", "color": "#0F172A"},
            "markArea": {"silent": True, "label": {"fontSize": 17, "fontWeight": "bold", "color": "#94A3B8", "position": "insideTop"},
                         "data": mark_area},
            "markLine": {"silent": True, "symbol": "none", "lineStyle": {"color": "#94A3B8", "type": "dashed", "width": 2},
                         "label": {"show": False}, "data": [{"xAxis": xm}, {"yAxis": ym}]}}]
    return _echart(opt, h, leg, d.get("source", ""))


def network(d, th):
    groups = d.get("groups", {})
    has_xy = all("x" in n for n in d["nodes"])
    nodes = []
    for n in d["nodes"]:
        c = _col(groups.get(n.get("group"), n.get("color")))
        item = {"name": n["name"], "symbolSize": n.get("size", 46), "symbol": n.get("shape", "circle"),
                "itemStyle": {"color": c, "borderColor": "#fff", "borderWidth": 4, "shadowBlur": 14, "shadowColor": c},
                "label": {"position": n.get("label", "bottom")}}
        if has_xy: item.update({"x": n["x"], "y": n["y"]})
        nodes.append(item)
    links = []
    for l in d["links"]:
        lk = {"source": l[0], "target": l[1]}
        if len(l) > 2 and l[2]:
            lk["label"] = {"show": True, "formatter": str(l[2]), "fontSize": 14, "fontWeight": "bold", "color": "#475569",
                           "backgroundColor": "#fff", "padding": [3, 7], "borderRadius": 6, "borderColor": "#E2E8F0", "borderWidth": 1}
        links.append(lk)
    layout = "none" if has_xy else d.get("graph_layout", "circular")
    sr = {"type": "graph", "layout": layout, "roam": False, "data": nodes, "links": links,
          "left": 80, "right": 90, "top": 60, "bottom": 105,
          "label": {"show": True, "fontSize": 17, "fontWeight": "bold", "color": "#0F172A"},
          "edgeSymbol": ["none", "arrow"] if d.get("arrows") else ["none", "none"], "edgeSymbolSize": 12,
          "lineStyle": {"color": "#94A3B8", "width": 2.5, "curveness": d.get("curveness", 0.12), "opacity": 0.85}}
    if layout == "force":
        sr["force"] = {"repulsion": 700, "edgeLength": [110, 170], "gravity": 0.2}
    if layout == "circular":
        sr["circular"] = {"rotateLabel": False}
    leg = _legend([(g, _col(c)) for g, c in groups.items()]) if groups and d.get("legend", True) else ""
    return _echart({"series": [sr]}, d.get("height", 520), leg, d.get("source", ""))


def sankey(d, th):
    nodes = [{"name": n["name"], "itemStyle": {"color": _col(n.get("color"), "slate")}} for n in d["nodes"]]
    sr = {"type": "sankey", "left": 16, "right": 150, "top": 16, "bottom": 16, "nodeWidth": 22, "nodeGap": 16,
          "layoutIterations": 0, "data": nodes, "links": [{"source": a, "target": b, "value": v} for a, b, v in d["links"]],
          "label": {"fontSize": 17, "fontWeight": "bold", "color": "#0F172A"},
          "lineStyle": {"color": "gradient", "opacity": 0.42, "curveness": 0.5}}
    return _echart({"series": [sr]}, d.get("height", 480), "", d.get("source", ""))


def timeline(d, th):
    ev = d["events"]
    cards_ = "".join(f'<div class="ev" style="{vars_(e.get("color"))}"><div class="dt">{esc(e["date"])}</div><div class="pin"></div>'
                     f'<div class="card"><div class="t">{esc(e["title"])}</div><div class="d">{esc(e.get("desc"))}</div>{ex(e)}</div></div>'
                     for e in ev)
    p2, s2 = pal(th.get("primary"), "indigo")[1], pal(th.get("secondary"), "cyan")[1]
    return (f'<style>{VIZ_CSS}</style><div class="tl" style="--p2:{p2};--s2:{s2};grid-template-columns:repeat({len(ev)},1fr)">'
            f'{cards_}</div>')


VIZ = {"chart", "network", "sankey"}


LAYOUTS = {"flow": flow, "cards": cards, "compare": compare, "matrix": matrix,
           "spectrum": spectrum, "triple": triple, "stack": stack, "bars": bars,
           "chart": chart, "network": network, "sankey": sankey, "timeline": timeline}


def title_html(t: str) -> str:
    # *강조* 표기를 그라데이션 강조로
    parts = esc(t).split("*")
    return "".join(f"<em>{p}</em>" if i % 2 else p for i, p in enumerate(parts))


def page(d: dict, th: dict) -> str:
    kicker = d.get("kicker") or th.get("book", "")
    sub = f'<div class="sub">{esc(d["subtitle"])}</div>' if d.get("subtitle") else ""
    note = (f'<div class="note"><span class="ic">💡</span><span>{esc(d["note"])}</span></div>' if d.get("note") else "")
    foot = f'<div class="foot"><span>{esc(th.get("book", ""))}</span><span>{esc(th.get("site", "wikidocs.net"))}</span></div>'
    mark = d.get("mark")
    if mark is None:
        m = re.match(r"(?:ch|p)(\d{2}(?:-\d+)?)", Path(d["file"]).stem)
        mark = m.group(1) if m else ""
    lib = f'<script src="{ECHARTS.as_uri()}"></script>' if d["layout"] in VIZ else ""
    return (f'<!doctype html><html><head><meta charset="utf-8"><style>{css(th)}</style>{lib}</head><body><div id="c">'
            f'<div class="topbar"></div><div class="mark">{esc(mark)}</div><div class="z">'
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
    if (j.wait) await page.waitForTimeout(j.wait);
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
            jobs.append({"html": str(h), "png": str(ASSETS / d["file"]), "name": d["file"],
                         "wait": 700 if d["layout"] in VIZ else 0})
        if not jobs:
            sys.exit("만들 이미지가 없습니다.")
        print(f"[이미지 생성] {len(jobs)}개")
        js = Path(tmp) / "shot.js"
        js.write_text(SHOT_JS, encoding="utf-8")
        subprocess.run(["node", str(js), json.dumps(jobs)], check=True, cwd=tmp)


if __name__ == "__main__":
    main()
