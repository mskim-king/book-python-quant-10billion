"""08-3. 머신러닝 팩터 — 릿지 회귀로 다음 달 수익률 예측 (numpy만 사용, 가상 데이터)"""
import numpy as np
import pandas as pd
from importlib import import_module

fx = import_module("05_factors")
prices, monthly = fx.prices, fx.monthly
cols = ["가치", "모멘텀", "퀄리티", "저변동성"]

X_rows, y_rows, dates = [], [], []
for i in range(24, len(prices) - 1):
    t, nxt = prices.index[i], prices.index[i + 1]
    f = fx.factor_scores(t)[cols]
    X_rows.append(f.values); y_rows.append(monthly.loc[nxt].values); dates.append(t)

def ridge(X, y, lam=10.0):
    return np.linalg.solve(X.T @ X + lam * np.eye(X.shape[1]), X.T @ y)

split = 60                                    # 앞 60개월 학습 → 이후 매달 확장하며 예측
spreads_ml, spreads_eq = [], []
for k in range(split, len(dates)):
    X = np.vstack(X_rows[:k]); y = np.concatenate(y_rows[:k])
    beta = ridge(X, y)
    pred = X_rows[k] @ beta
    eq_score = X_rows[k].mean(axis=1)         # 비교: 단순 평균(멀티팩터)
    fwd = y_rows[k]
    for score, bucket in [(pred, spreads_ml), (eq_score, spreads_eq)]:
        q = pd.qcut(score, 5, labels=False)
        bucket.append(fwd[q == 4].mean() - fwd[q == 0].mean())
print("마지막 학습 가중치(합=1로 정규화):", {c: round(float(b), 2) for c, b in zip(cols, beta / np.abs(beta).sum())})
print(f"검증 {len(spreads_ml)}개월 · 상위-하위 월평균 차이")
print(f"  릿지 회귀 : {np.mean(spreads_ml):.4f} (플러스 달 {np.mean(np.array(spreads_ml) > 0):.0%})")
print(f"  단순 평균 : {np.mean(spreads_eq):.4f} (플러스 달 {np.mean(np.array(spreads_eq) > 0):.0%})")
