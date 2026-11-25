"""06-1. 비중 결정 — 동일비중, 변동성 역가중, 최소분산 (가상 데이터)"""
import numpy as np
import pandas as pd
from sample_data import make_assets

ret = make_assets().pct_change().dropna()
train, test = ret.iloc[:756], ret.iloc[756:]          # 앞 3년으로 비중 계산, 뒤 2년에 적용
cov = train.cov().values * 252
n = len(train.columns)

w_eq = np.ones(n) / n
w_iv = (1 / np.sqrt(np.diag(cov))); w_iv /= w_iv.sum()
inv = np.linalg.inv(cov); w_mv = inv @ np.ones(n); w_mv /= w_mv.sum()   # 최소분산(공매도 허용 공식)

def risk_contrib(w):
    port_var = w @ cov @ w
    return w * (cov @ w) / port_var                    # 각 자산이 전체 위험에서 차지하는 비율

rows = {}
for name, w in {"동일비중": w_eq, "변동성역가중": w_iv, "최소분산": w_mv}.items():
    r = test.values @ w
    rows[name] = dict(zip([f"비중_{c}" for c in ret.columns], w.round(3)),
                      **{"예상변동성": np.sqrt(w @ cov @ w), "실현변동성(검증)": r.std() * np.sqrt(252),
                         "주식 위험기여": risk_contrib(w)[0]})
print(pd.DataFrame(rows).T.round(3))
