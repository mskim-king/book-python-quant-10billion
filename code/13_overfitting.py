"""05-4. 과최적화와 검증 — 학습 구간 최고 파라미터는 검증 구간에서도 좋을까?

추세가 없는 가상 주가(무작위 보행) 50개로 같은 실험을 반복합니다.
진짜 우위가 없는 데이터에서도 '학습 1위' 조합은 늘 좋아 보입니다.
"""
import numpy as np
import pandas as pd
from sample_data import make_prices
from importlib import import_module

eng = import_module("10_backtest_engine")
grid = [(f, s) for f in [5, 10, 20, 30, 40] for s in [60, 90, 120, 150, 200]]
rows = []
for seed in range(50):
    price = make_prices(days=1260, seed=100 + seed)["B"]
    split = price.index[756]                                # 앞 3년 학습, 뒤 2년 검증
    res = []
    for fast, slow in grid:
        sig = (price.rolling(fast).mean() > price.rolling(slow).mean()).astype(float)
        net = eng.backtest(price, sig, cost_bps=15)["net"]
        res.append((eng.report(net[:split])["샤프(무위험0)"], eng.report(net[split:])["샤프(무위험0)"]))
    res = np.array(res)
    best = res[:, 0].argmax()
    rows.append({"학습1위_학습샤프": res[best, 0], "학습1위_검증샤프": res[best, 1],
                 "전체평균_검증샤프": res[:, 1].mean()})
r = pd.DataFrame(rows)
print(f"반복 {len(r)}회 · 파라미터 조합 {len(grid)}개씩")
print(r.mean().round(2).to_string())
print(f"\n학습1위가 검증에서 전체 평균보다 나았던 비율: {(r['학습1위_검증샤프'] > r['전체평균_검증샤프']).mean():.0%}")
