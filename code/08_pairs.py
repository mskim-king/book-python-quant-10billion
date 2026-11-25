"""04-3. 페어 트레이딩 — 함께 움직이는 두 종목의 차이(스프레드) 거래 (가상 데이터)"""
import numpy as np
import pandas as pd
from sample_data import make_pair

df = make_pair()
train, test = df.iloc[:252], df.iloc[252:]

# 1) 학습 구간에서 헤지비율(beta) 추정: Y ≈ a + b·X (최소제곱)
b, a = np.polyfit(train["X"], train["Y"], 1)
print(f"헤지비율 b = {b:.3f}, 절편 a = {a:.2f}")
spread_train = train["Y"] - (a + b * train["X"])
mu, sd = spread_train.mean(), spread_train.std()

# 2) 검증 구간: 스프레드 z가 ±2를 넘으면 진입, 0 근처로 돌아오면 청산
spread = test["Y"] - (a + b * test["X"])
z = (spread - mu) / sd
pos = pd.Series(0, index=test.index)
cur = 0
for i, zz in enumerate(z):
    if cur == 0 and zz > 2: cur = -1          # Y 비쌈: Y 매도, X 매수
    elif cur == 0 and zz < -2: cur = 1        # Y 쌈: Y 매수, X 매도
    elif cur != 0 and abs(zz) < 0.5: cur = 0
    pos.iloc[i] = cur
pnl = pos.shift(1).fillna(0) * spread.diff().fillna(0)   # 스프레드 1단위 보유 손익
print(f"검증 구간 거래 횟수: {int((pos.diff().abs() > 0).sum())}")
print(f"누적 손익(스프레드 단위): {pnl.sum():.2f}")
print(f"스프레드 반감기(일): {np.log(0.5) / np.log(np.corrcoef(spread[1:], spread[:-1])[0,1]):.1f}")
