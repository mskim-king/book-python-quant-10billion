"""04-4. 자산배분 — 60/40, 동일비중, 변동성 역가중 (월 리밸런싱, 가상 데이터)"""
import numpy as np
import pandas as pd
from sample_data import make_assets

px = make_assets()
ret = px.pct_change().dropna()

def backtest(weight_fn) -> pd.Series:
    out, w = [], None
    for d in ret.index:
        if w is None or d.month != prev.month:          # 매월 첫 거래일 리밸런싱
            w = weight_fn(ret.loc[:d].iloc[:-1])
        r = (ret.loc[d] * w).sum()
        w = w * (1 + ret.loc[d]); w = w / w.sum()       # 가격 변화로 비중이 흘러감
        out.append(r); prev = d
    return pd.Series(out, index=ret.index)

prev = ret.index[0]
fixed = lambda w: (lambda h: pd.Series(w, index=px.columns))
inv_vol = lambda h: (1 / h.tail(60).std()) / (1 / h.tail(60).std()).sum() if len(h) > 60 else pd.Series(1/3, index=px.columns)
strategies = {"주식100%": fixed([1, 0, 0]), "60/40": fixed([0.6, 0.4, 0]),
              "동일비중": fixed([1/3, 1/3, 1/3]), "변동성역가중": inv_vol}
rows = {}
for name, fn in strategies.items():
    prev = ret.index[0]
    r = backtest(fn)
    eq = (1 + r).cumprod(); yrs = len(r) / 252
    rows[name] = {"CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "변동성": r.std() * np.sqrt(252),
                  "MDD": (eq / eq.cummax() - 1).min()}
print(pd.DataFrame(rows).T.round(3))
print("\n자산 간 상관계수\n", ret.corr().round(2))
