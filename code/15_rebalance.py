"""06-2. 리밸런싱 — 60/40 포트폴리오를 안 함·분기·월·밴드(±5%p) 방식으로 비교"""
import numpy as np
import pandas as pd
from sample_data import make_assets

px = make_assets()[["주식", "채권"]]
ret = px.pct_change().dropna()
target = np.array([0.6, 0.4])

def run(rule):
    w, out, trades, prev = target.copy(), [], 0.0, ret.index[0]
    for d, r in ret.iterrows():
        need = (rule == "월" and d.month != prev.month) or \
               (rule == "분기" and d.month != prev.month and d.month in (1, 4, 7, 10)) or \
               (rule == "밴드" and abs(w[0] - target[0]) > 0.05)
        if need:
            trades += np.abs(w - target).sum() / 2; w = target.copy()
        out.append((w * r.values).sum())
        w = w * (1 + r.values); w /= w.sum(); prev = d
    s = pd.Series(out, index=ret.index); eq = (1 + s).cumprod()
    return {"CAGR": eq.iloc[-1] ** (252 / len(s)) - 1, "변동성": s.std() * np.sqrt(252),
            "MDD": (eq / eq.cummax() - 1).min(), "누적매매비율": trades, "최종 주식비중": w[0]}

print(pd.DataFrame({k: run(k) for k in ["안 함", "분기", "월", "밴드"]}).T.round(3))
