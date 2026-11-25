"""04-2. 평균회귀 — 볼린저밴드 (가상 데이터)"""
import pandas as pd
from sample_data import make_prices

price = make_prices()["B"]
ret = price.pct_change().fillna(0)
ma, sd = price.rolling(20).mean(), price.rolling(20).std()
z = (price - ma) / sd                         # 평균에서 표준편차 몇 개만큼 떨어졌나

pos = pd.Series(0.0, index=price.index)
holding = 0
for i, (d, zz) in enumerate(z.items()):
    if holding == 0 and zz < -2:              # 아래 밴드 이탈 → 매수
        holding = 1
    elif holding == 1 and zz > 0:             # 평균 회복 → 매도
        holding = 0
    pos.iloc[i] = holding
strat = pos.shift(1).fillna(0) * ret

eq_bh, eq_st = (1 + ret).cumprod(), (1 + strat).cumprod()
print(pd.DataFrame({
    "누적수익률": [eq_bh.iloc[-1] - 1, eq_st.iloc[-1] - 1],
    "MDD": [(eq_bh / eq_bh.cummax() - 1).min(), (eq_st / eq_st.cummax() - 1).min()],
    "보유비중": [1.0, pos.mean()],
}, index=["매수후보유", "볼린저 평균회귀"]).round(3))
print("\n진입 횟수:", int((pos.diff() == 1).sum()))
