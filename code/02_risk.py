"""01-3. 위험 측정 — 변동성, 최대낙폭(MDD), 샤프지수"""
import numpy as np
from sample_data import make_prices

prices = make_prices()
ret = prices.pct_change().dropna()

# 1) 연율화 변동성: 일간 수익률 표준편차 × √252
vol = ret.std() * np.sqrt(252)

# 2) 최대낙폭(MDD): 지금까지의 최고점 대비 가장 크게 떨어진 비율
running_max = prices.cummax()
drawdown = prices / running_max - 1
mdd = drawdown.min()

# 3) 샤프지수: (연수익률 - 무위험수익률) / 연율화 변동성
risk_free = 0.03  # 가정: 연 3%
annual_return = (1 + ret.mean()) ** 252 - 1
sharpe = (annual_return - risk_free) / vol

summary = (
    __import__("pandas").DataFrame(
        {"연수익률": annual_return, "변동성": vol, "MDD": mdd, "샤프지수": sharpe}
    ).round(3)
)
print(summary)
assert (mdd <= 0).all()
