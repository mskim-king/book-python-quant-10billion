"""03장. 팩터 계산과 검증 — 가치·모멘텀·퀄리티·저변동성·멀티팩터 (가상 데이터)

매달 말 팩터 점수로 종목을 5개 그룹(분위)으로 나누고, 다음 달 수익률을 비교합니다.
"""
import numpy as np
import pandas as pd
from sample_data import make_universe

prices, fund = make_universe(n=200, months=120)
monthly = prices.pct_change()

def zscore(s: pd.Series) -> pd.Series:
    return (s - s.mean()) / s.std()

def factor_scores(t) -> pd.DataFrame:
    """t 시점까지의 정보만으로 점수 계산 (미래 정보 사용 금지)"""
    p = prices.loc[:t]
    f = pd.DataFrame(index=prices.columns)
    f["가치"] = zscore(-np.log(fund["PBR"]))                          # PBR 낮을수록 ↑
    f["모멘텀"] = zscore(p.iloc[-2] / p.iloc[-13] - 1)                 # 12-1개월 수익률
    f["퀄리티"] = zscore(zscore(fund["ROE"]) - zscore(fund["부채비율"]))  # ROE↑ 부채↓
    f["저변동성"] = zscore(-monthly.loc[:t].tail(24).std())             # 24개월 변동성 ↓
    f["멀티팩터"] = zscore(f[["가치", "모멘텀", "퀄리티", "저변동성"]].mean(axis=1))
    return f

if __name__ == "__main__":
    last = factor_scores(prices.index[-1])
    print("마지막 달 팩터 점수 (멀티팩터 상위 5종목)")
    print(last.sort_values("멀티팩터", ascending=False).head(5).round(2), "\n")

    spreads = {c: [] for c in last.columns}
    for i in range(24, len(prices) - 1):                  # 24개월 이후부터 매달 리밸런싱
        t, nxt = prices.index[i], prices.index[i + 1]
        f, fwd = factor_scores(t), monthly.loc[nxt]
        for c in f.columns:
            q = pd.qcut(f[c], 5, labels=False)
            spreads[c].append(fwd[q == 4].mean() - fwd[q == 0].mean())
    s = pd.DataFrame(spreads)
    out = pd.DataFrame({
        "월평균 차이(상위-하위)": s.mean(),
        "연환산": s.mean() * 12,
        "플러스인 달 비율": (s > 0).mean(),
        "변동성(연)": s.std() * np.sqrt(12),
    })
    out["위험대비(차이/변동성)"] = out["연환산"] / out["변동성(연)"]
    print(f"검증 기간: {len(s)}개월")
    print(out.round(3))
    print("\n팩터 점수 간 상관계수 (마지막 달)")
    print(last.drop(columns="멀티팩터").corr().round(2))
