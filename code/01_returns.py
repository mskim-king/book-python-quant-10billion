"""01-2. 수익률 계산 — 단순수익률, 로그수익률, 누적수익률, 연평균수익률(CAGR)"""
import numpy as np
from sample_data import make_prices

prices = make_prices()
print("가상 종가 (앞 3일)\n", prices.head(3), "\n")

# 1) 일간 단순수익률: (오늘 가격 / 어제 가격) - 1
simple = prices.pct_change().dropna()

# 2) 일간 로그수익률: ln(오늘 / 어제) — 기간별로 더할 수 있어 계산이 편함
log_ret = np.log(prices / prices.shift(1)).dropna()

# 3) 누적수익률: 기간 동안 (1 + 일간수익률)을 모두 곱한 뒤 1을 뺌
cumulative = (1 + simple).prod() - 1

# 4) 연평균 복리수익률(CAGR): (마지막/처음)^(1/연수) - 1
years = len(prices) / 252
cagr = (prices.iloc[-1] / prices.iloc[0]) ** (1 / years) - 1

print("일간 단순수익률 (앞 3일)\n", simple.head(3).round(4), "\n")
print("누적수익률\n", cumulative.round(4), "\n")
print(f"기간: {years:.1f}년")
print("연평균 복리수익률(CAGR)\n", cagr.round(4))

# 검산: 로그수익률의 합 = ln(마지막/처음)
assert np.allclose(log_ret.sum(), np.log(prices.iloc[-1] / prices.iloc[0]))
