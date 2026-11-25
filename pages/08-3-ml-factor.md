<!--
**상태**: 🔵 검토 중
**분류**: 08. AI 퀀트
**태그**: #AI #ML
**작성일**: 2026-11-22
-->
> 📅 **최종 확인**: 2026-11-25

03장에서는 팩터를 **같은 무게**로 섞었습니다. 머신러닝을 쓰면 과거 데이터로 **어떤 팩터에 얼마의 무게를 줄지** 배울 수 있습니다. 이 페이지에서는 가장 기본적인 모델인 **릿지 회귀**를 numpy만으로 구현해 비교합니다.

## 요약

- 매달 팩터 점수(입력)로 다음 달 수익률(정답)을 예측하는 모델을 학습합니다.
- **확장 창**: 앞 60개월로 학습하고, 이후 매달 학습 데이터를 늘려 가며 다음 달을 예측합니다(미래 정보 금지).
- 가상 데이터 결과: 릿지 회귀가 단순 평균보다 평균 차이는 컸지만, **플러스인 달은 둘 다 49%**로 꾸준함의 차이는 없었습니다.

## 코드

전체 코드는 `code/17_ml_factor.py`에 있습니다.

```python
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
```

## 실행 결과

```text
마지막 학습 가중치(합=1로 정규화): {'가치': 0.19, '모멘텀': 0.34, '퀄리티': 0.06, '저변동성': 0.4}
검증 35개월 · 상위-하위 월평균 차이
  릿지 회귀 : 0.0043 (플러스 달 49%)
  단순 평균 : 0.0006 (플러스 달 49%)
```

## 해석

- 모델은 저변동성(0.40)과 모멘텀(0.34)에 큰 무게를, 퀄리티(0.06)에 작은 무게를 주었습니다. 03장 검증에서 효과가 컸던 순서와 비슷합니다.
- 월평균 차이는 릿지(0.43%)가 단순 평균(0.06%)보다 컸지만, 검증 기간이 **35개월로 짧고** 플러스인 달 비율은 같았습니다. 이 정도로는 "머신러닝이 더 낫다"고 말할 수 없습니다.
- 복잡한 모델일수록 과최적화 위험이 커집니다(05-4). 단순한 결합을 기준선으로 두고, 그보다 **확실히** 나을 때만 복잡한 모델을 씁니다.

## 머신러닝 팩터의 원칙

| 원칙 | 내용 |
|---|---|
| 시점 분리 | 학습 데이터는 항상 예측 시점 이전 |
| 기준선 비교 | 단순 평균·단일 팩터보다 나은지 확인 |
| 규제(regularization) | 릿지의 λ처럼 가중치를 작게 유지해 과적합 억제 |
| 해석 | 가중치·중요도를 보고 경제적으로 말이 되는지 확인 |
| 충분한 검증 기간 | 수십 개월은 짧음 — 결과를 보수적으로 해석 |

> 모든 수치는 가상 데이터로 계산한 결과이며 투자 권유가 아닙니다. 과거 성과는 미래 수익을 보장하지 않습니다.

## 실무 체크포인트

- [ ] 학습 데이터가 예측 시점 이전으로만 구성되었는가
- [ ] 단순한 기준선과 비교했는가
- [ ] 검증 기간이 충분한지, 결과를 과장하지 않았는가

## 근거·출처

| 구분 | 출처 | 비고 |
|---|---|---|
| 논문 | Gu, S., Kelly, B. & Xiu, D. (2020). Empirical Asset Pricing via Machine Learning. *Review of Financial Studies* | 머신러닝과 수익률 예측 |

## 관련 페이지

- 08-1. 프롬프트로 전략 코드 만들기
- 08-2. 뉴스·공시 LLM 분석
