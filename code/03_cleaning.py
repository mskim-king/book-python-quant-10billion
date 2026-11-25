"""02-4. 결측치·수정주가·상장폐지 처리"""
import numpy as np
import pandas as pd

dates = pd.bdate_range("2025-03-03", periods=8)
# 가상 원자료: 거래정지로 빈 날(NaN), 3/6에 1:2 액면분할(가격이 절반이 됨)
raw = pd.Series([50_000, 51_000, np.nan, 26_000, 25_500, 26_500, np.nan, 27_000], index=dates, name="종가")
print("① 원자료\n", raw, "\n")

# 1) 결측치: 앞의 값으로 채우기(ffill) — 단, 몇 칸이 비었는지 기록해 둔다
filled = raw.ffill()
print("결측 개수:", int(raw.isna().sum()))

# 2) 수정주가: 분할 이전 가격을 분할비율로 나눠 연속성을 맞춘다
split_date, ratio = pd.Timestamp("2025-03-06"), 2
adjusted = filled.copy()
adjusted[adjusted.index < split_date] /= ratio
compare = pd.DataFrame({"원주가": filled, "수정주가": adjusted})
compare["원주가_수익률"] = compare["원주가"].pct_change().round(3)
compare["수정_수익률"] = compare["수정주가"].pct_change().round(3)
print("\n② 수정주가 비교\n", compare, "\n")

# 3) 상장폐지(생존편향): 오늘 살아 있는 종목만 쓰면 결과가 부풀려진다
universe = pd.DataFrame({
    "종목": ["가", "나", "다", "라", "마"],
    "기간수익률": [0.35, 0.12, -0.05, -0.90, -1.00],
    "상장상태": ["상장", "상장", "상장", "상장폐지", "상장폐지"],
})
alive_only = universe.loc[universe["상장상태"] == "상장", "기간수익률"].mean()
all_stocks = universe["기간수익률"].mean()
print("③ 생존편향")
print(f"  살아남은 종목만 평균: {alive_only:.1%}")
print(f"  상장폐지 포함 평균:   {all_stocks:.1%}")
assert alive_only > all_stocks
