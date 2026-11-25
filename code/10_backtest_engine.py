"""05-1. 간단한 백테스트 엔진 — 신호 → 다음날 포지션 → 비용 차감 → 성과 지표"""
import numpy as np
import pandas as pd
from sample_data import make_prices


def backtest(price: pd.Series, signal: pd.Series, cost_bps: float = 0.0) -> pd.DataFrame:
    """signal(0~1)을 '다음 날' 비중으로 사용. cost_bps: 매매금액 대비 편도 비용(bp)"""
    ret = price.pct_change().fillna(0)
    pos = signal.shift(1).fillna(0)                 # 미래참조 방지: 하루 늦게 적용
    turnover = pos.diff().abs().fillna(pos.abs())   # 비중 변화량 = 매매금액 비율
    cost = turnover * cost_bps / 10_000
    net = pos * ret - cost
    return pd.DataFrame({"pos": pos, "gross": pos * ret, "cost": cost, "net": net})


def report(r: pd.Series) -> dict:
    eq = (1 + r).cumprod()
    yrs = len(r) / 252
    vol = r.std() * np.sqrt(252)
    cagr = eq.iloc[-1] ** (1 / yrs) - 1
    return {"CAGR": cagr, "변동성": vol, "샤프(무위험0)": cagr / vol if vol else np.nan,
            "MDD": (eq / eq.cummax() - 1).min()}


if __name__ == "__main__":
    price = make_prices()["A"]
    signal = (price.rolling(20).mean() > price.rolling(60).mean()).astype(float)
    bt = backtest(price, signal, cost_bps=15)
    print("엔진 출력 (앞 3행)\n", bt.dropna().iloc[60:63].round(5), "\n")
    print(pd.DataFrame({"비용 전": report(bt["gross"]), "비용 후(15bp)": report(bt["net"]),
                        "매수후보유": report(price.pct_change().fillna(0))}).T.round(3))
    print("\n연간 회전율(배):", round(bt["pos"].diff().abs().sum() / (len(bt) / 252), 1))
