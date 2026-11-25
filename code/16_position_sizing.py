"""06-3. 낙폭 관리 — 변동성 타기팅(목표 변동성 15%)으로 위험 크기 조절"""
import numpy as np
import pandas as pd
from sample_data import make_prices

ret = make_prices()["C"].pct_change().dropna()
realized = ret.rolling(20).std() * np.sqrt(252)
weight = (0.15 / realized).clip(upper=1.0).shift(1).fillna(0)   # 최대 100%, 하루 늦게 적용
scaled = weight * ret

def s(r):
    eq = (1 + r).cumprod()
    return {"변동성": r.std() * np.sqrt(252), "MDD": (eq / eq.cummax() - 1).min(), "최종자산(시작=1)": eq.iloc[-1]}
print(pd.DataFrame({"그대로 보유": s(ret), "변동성 타기팅 15%": s(scaled)}).T.round(3))
print(f"\n평균 투자비중: {weight[20:].mean():.1%}")
