"""05-3. 미래참조편향 — 같은 날 종가로 신호를 만들고 같은 날 수익을 먹으면 생기는 착시"""
import pandas as pd
from sample_data import make_prices
from importlib import import_module

eng = import_module("10_backtest_engine")
price = make_prices()["B"]
ret = price.pct_change().fillna(0)
signal = (ret > 0).astype(float)          # '오늘 올랐으면 보유' — 오늘이 끝나야 알 수 있는 정보

wrong = signal * ret                       # ❌ 신호를 같은 날 적용 (미래참조)
right = eng.backtest(price, signal)["net"] # ✅ 다음 날 적용
print(pd.DataFrame({"미래참조(잘못)": eng.report(wrong), "다음날 적용(올바름)": eng.report(right)}).T.round(3))
