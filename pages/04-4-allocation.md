<!--
**상태**: 🔵 검토 중
**분류**: 04. 전략
**태그**: #전략 #자산배분
**작성일**: 2026-11-22
-->
> 📅 **최종 확인**: 2026-11-25

**자산배분**은 종목 고르기보다 먼저 "주식·채권·금 등 자산을 얼마씩 나눌까"를 정하는 전략입니다. 서로 다르게 움직이는 자산을 섞으면 전체 흔들림이 줄어듭니다.

## 요약

- 가상 데이터로 주식100%, 60/40, 동일비중, 변동성 역가중을 **매월 리밸런싱**하며 비교합니다.
- 주식 비중을 낮출수록 변동성과 MDD가 줄지만 수익률도 줄어듭니다(수익과 위험의 교환).
- 어떤 배분이 최선인지는 **내가 견딜 수 있는 낙폭**에 따라 다릅니다.

![계란을 한 바구니에 담지 말라던데요](../assets/p04-4-chat-eggs.png)

## 코드

전체 코드는 `code/09_allocation.py`에 있습니다.

```python
"""04-4. 자산배분 — 60/40, 동일비중, 변동성 역가중 (월 리밸런싱, 가상 데이터)"""
import numpy as np
import pandas as pd
from sample_data import make_assets

px = make_assets()
ret = px.pct_change().dropna()

def backtest(weight_fn) -> pd.Series:
    out, w = [], None
    for d in ret.index:
        if w is None or d.month != prev.month:          # 매월 첫 거래일 리밸런싱
            w = weight_fn(ret.loc[:d].iloc[:-1])
        r = (ret.loc[d] * w).sum()
        w = w * (1 + ret.loc[d]); w = w / w.sum()       # 가격 변화로 비중이 흘러감
        out.append(r); prev = d
    return pd.Series(out, index=ret.index)

prev = ret.index[0]
fixed = lambda w: (lambda h: pd.Series(w, index=px.columns))
inv_vol = lambda h: (1 / h.tail(60).std()) / (1 / h.tail(60).std()).sum() if len(h) > 60 else pd.Series(1/3, index=px.columns)
strategies = {"주식100%": fixed([1, 0, 0]), "60/40": fixed([0.6, 0.4, 0]),
              "동일비중": fixed([1/3, 1/3, 1/3]), "변동성역가중": inv_vol}
rows = {}
for name, fn in strategies.items():
    prev = ret.index[0]
    r = backtest(fn)
    eq = (1 + r).cumprod(); yrs = len(r) / 252
    rows[name] = {"CAGR": eq.iloc[-1] ** (1 / yrs) - 1, "변동성": r.std() * np.sqrt(252),
                  "MDD": (eq / eq.cummax() - 1).min()}
print(pd.DataFrame(rows).T.round(3))
print("\n자산 간 상관계수\n", ret.corr().round(2))
```

## 실행 결과

```text
         CAGR    변동성    MDD
주식100%  0.171  0.177 -0.252
60/40   0.099  0.104 -0.174
동일비중    0.049  0.083 -0.260
변동성역가중  0.021  0.063 -0.211

자산 간 상관계수
       주식    채권     금
주식  1.00 -0.21  0.12
채권 -0.21  1.00  0.22
금   0.12  0.22  1.00
```

## 해석

- **60/40**은 주식100%보다 수익(CAGR 9.9% vs 17.1%)은 낮지만 변동성(10.4%)과 MDD(−17.4%)가 크게 줄었습니다.
- 가상 데이터에서 금과 채권의 기대수익을 낮게 가정했기 때문에, 그 비중이 큰 **동일비중·변동성역가중**은 수익이 낮게 나왔습니다. 결과는 가정을 그대로 따릅니다.
- 주식과 채권의 상관계수가 **−0.21**로 음수라, 섞으면 흔들림이 줄어듭니다.

## 대표 자산배분 방식

| 방식 | 규칙 | 특징 |
|---|---|---|
| 60/40 | 주식 60%, 채권 40% | 가장 오래된 기준선 |
| 동일비중 | 자산마다 같은 비중 | 단순, 예측 불필요 |
| 변동성 역가중 | 덜 흔들리는 자산에 더 많이 | 위험을 고르게 나눔 (06-1) |
| 위험 균형 | 자산별 위험 기여를 똑같이 | 채권 비중이 커지는 경향 |

> 모든 수치는 가상 데이터로 계산한 결과이며 투자 권유가 아닙니다. 과거 성과는 미래 수익을 보장하지 않습니다.

## 실무 체크포인트

- [ ] 내가 견딜 수 있는 최대 낙폭을 먼저 정했는가
- [ ] 자산 간 상관계수를 확인했는가
- [ ] 리밸런싱 주기와 비용을 정했는가 (06-2)

## 관련 페이지

- 04-1. 추세추종
- 04-2. 평균회귀
- 04-3. 페어 트레이딩
