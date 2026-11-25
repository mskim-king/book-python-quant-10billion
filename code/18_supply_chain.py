"""09-2. 공급망 관계로 팩터 만들기 — 고객사의 지난달 수익률이 공급사에 전해지는가 (가상 데이터)"""
import numpy as np
import pandas as pd

rng = np.random.default_rng(3)
months, n_cust, n_sup = 120, 30, 90
cust = rng.normal(0.006, 0.07, (months, n_cust))                 # 고객사(완성품) 월수익률
links = {s: rng.choice(n_cust, size=rng.integers(1, 4), replace=False) for s in range(n_sup)}
sup = np.zeros((months, n_sup))
for t in range(1, months):
    for s, cs in links.items():                                  # 가정: 고객사 지난달 수익의 30%가 늦게 반영
        sup[t, s] = 0.3 * cust[t - 1, cs].mean() + rng.normal(0.005, 0.06)

# 공급망 모멘텀 점수 = 연결된 고객사의 지난달 평균 수익률
spread = []
for t in range(1, months - 1):
    score = np.array([cust[t, links[s]].mean() for s in range(n_sup)])
    q = pd.qcut(score, 5, labels=False)
    spread.append(sup[t + 1, q == 4].mean() - sup[t + 1, q == 0].mean())
spread = np.array(spread)
print("공급사 예시 연결:", {f"공급사{s}": [f"고객사{c}" for c in links[s]] for s in range(3)})
print(f"상위-하위 월평균 차이: {spread.mean():.4f} · 플러스 달 비율: {(spread > 0).mean():.0%}")
own = np.array([pd.Series(sup[1:, s]).autocorr() for s in range(n_sup)])
print(f"참고) 공급사 자기 수익률의 1개월 자기상관 평균: {own.mean():.3f}")
