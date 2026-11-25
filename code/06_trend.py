"""04-1. 추세추종 — 이동평균 교차 전략 (가상 데이터)"""
import numpy as np
import pandas as pd
from sample_data import make_prices

price = make_prices()["C"]
ret = price.pct_change().fillna(0)

short, long = price.rolling(20).mean(), price.rolling(120).mean()
signal = (short > long).astype(int)          # 단기선이 장기선 위면 보유(1), 아니면 현금(0)
position = signal.shift(1).fillna(0)         # 오늘 신호로 '내일' 매매 → 미래참조 방지
strat = position * ret

def stats(r: pd.Series) -> dict:
    eq = (1 + r).cumprod()
    years = len(r) / 252
    return {"누적수익률": eq.iloc[-1] - 1, "CAGR": eq.iloc[-1] ** (1 / years) - 1,
            "MDD": (eq / eq.cummax() - 1).min(), "보유비중": None}

res = pd.DataFrame({"매수후보유": stats(ret), "이동평균교차": stats(strat)}).T
res.loc["매수후보유", "보유비중"] = 1.0
res.loc["이동평균교차", "보유비중"] = position.mean()
print(res.astype(float).round(3))
print("\n매매 횟수:", int(position.diff().abs().sum()))
