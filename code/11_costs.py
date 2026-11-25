"""05-2. 거래비용과 슬리피지 — 같은 전략도 비용과 매매 빈도에 따라 결과가 바뀐다"""
import pandas as pd
from sample_data import make_prices
from importlib import import_module

eng = import_module("10_backtest_engine")
price = make_prices()["A"]
rows = []
for fast, slow in [(5, 20), (20, 60), (60, 120)]:
    sig = (price.rolling(fast).mean() > price.rolling(slow).mean()).astype(float)
    for bps in [0, 15, 30, 50]:
        bt = eng.backtest(price, sig, cost_bps=bps)
        rows.append({"전략": f"{fast}/{slow}일", "편도비용(bp)": bps,
                     "연회전율": bt["pos"].diff().abs().sum() / 3,
                     "CAGR": eng.report(bt["net"])["CAGR"]})
t = pd.DataFrame(rows).pivot(index="전략", columns="편도비용(bp)", values="CAGR")
t.insert(0, "연회전율(배)", pd.DataFrame(rows).groupby("전략")["연회전율"].first().round(1))
print("비용별 CAGR (가상 데이터)")
print(t.round(3))
