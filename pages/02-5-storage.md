<!--
**상태**: 🔵 검토 중
**분류**: 02. 데이터 수집·정제
**태그**: #데이터 #저장
**작성일**: 2026-11-22
-->
> 📅 **최종 확인**: 2026-11-25

데이터를 매번 새로 받으면 느리고, 소스가 바뀌면 과거 결과를 재현할 수 없습니다. 이 페이지에서는 받은 데이터를 **CSV**와 **SQLite**(파이썬 표준 라이브러리)로 저장하고 다시 읽는 방법을 다룹니다.

## 요약

- 처음에는 **CSV**로 충분합니다. 날짜를 인덱스로 저장하고 읽을 때 날짜로 되돌립니다.
- 종목·기간으로 골라 읽어야 한다면 **SQLite**에 '긴 형식(날짜·종목·값)'으로 저장합니다.
- 저장할 때 **수집일·소스·수정주가 여부**를 함께 기록하면 나중에 결과를 재현할 수 있습니다.

## 형식별 비교

| 형식 | 장점 | 단점 | 이럴 때 |
|---|---|---|---|
| CSV | 어디서나 열림, 단순 | 크면 느림, 형식 정보 손실 | 종목 수십 개, 학습용 |
| SQLite | 설치 불필요(표준 라이브러리), SQL로 골라 읽기 | 동시 쓰기 약함 | 종목 수백~수천 개, 개인 프로젝트 |
| Parquet | 빠르고 작음, 형식 보존 | 별도 라이브러리(pyarrow) 필요 | 대용량 |

## 코드

전체 코드는 `code/04_storage.py`에 있습니다.

```python
"""02-5. 데이터 저장과 관리 — CSV와 SQLite(표준 라이브러리)"""
import sqlite3
from pathlib import Path
import pandas as pd
from sample_data import make_prices

out = Path("data"); out.mkdir(exist_ok=True)
prices = make_prices()

# 1) CSV: 가장 단순한 저장. 날짜를 인덱스로 저장하고 읽을 때 날짜로 되돌린다
prices.to_csv(out / "prices.csv", index_label="date")
back = pd.read_csv(out / "prices.csv", index_col="date", parse_dates=True)
print("CSV 왕복 후 동일한가:", back.equals(prices.astype(back.dtypes.iloc[0])))

# 2) SQLite: 종목·날짜로 골라 읽기 쉬운 '긴 형식(long)' 테이블
long = prices.reset_index(names="date").melt(id_vars="date", var_name="ticker", value_name="close")
long["date"] = long["date"].dt.strftime("%Y-%m-%d")
with sqlite3.connect(out / "quant.db") as con:
    long.to_sql("prices", con, if_exists="replace", index=False)
    con.execute("CREATE INDEX IF NOT EXISTS idx_t_d ON prices(ticker, date)")
    q = "SELECT ticker, COUNT(*) AS 일수, MIN(date) AS 시작, MAX(date) AS 끝 FROM prices GROUP BY ticker"
    print(pd.read_sql(q, con))
    one = pd.read_sql("SELECT date, close FROM prices WHERE ticker='B' AND date>='2025-11-01'", con)
    print("\nB 종목 최근 행 수:", len(one))
```

## 실행 결과

```text
CSV 왕복 후 동일한가: True
  ticker   일수          시작           끝
0      A  756  2023-01-02  2025-11-24
1      B  756  2023-01-02  2025-11-24
2      C  756  2023-01-02  2025-11-24

B 종목 최근 행 수: 16
```

## 해석

- CSV로 저장했다가 다시 읽은 표가 원본과 **같습니다**(`True`). 날짜를 `parse_dates`로 되돌리는 것이 핵심입니다.
- SQLite에는 종목 3개 × 756일이 긴 형식으로 들어갔고, `(ticker, date)` 색인 덕분에 "B 종목 11월 이후"처럼 필요한 부분만 빠르게 읽습니다.

## 폴더 구조 예시

```text
quant-study/
├─ data/
│   ├─ raw/        ← 받은 그대로 (수정하지 않음)
│   ├─ clean/      ← 결측·수정주가 처리 후
│   └─ quant.db    ← 분석용 SQLite
└─ code/
```

[[TIP("원자료는 지우지 마세요")]]

`raw` 폴더의 원자료는 그대로 두고, 정제 결과는 따로 저장하세요. 정제 방법을 바꿔도 처음부터 다시 받지 않아도 됩니다.

[[/TIP]]

## 실무 체크포인트

- [ ] 원자료와 정제 데이터를 나눠 저장하는가
- [ ] 수집일·소스·수정주가 여부를 기록했는가
- [ ] 다시 읽은 데이터가 원본과 같은지 확인했는가

## 관련 페이지

- 02-1. 국내·해외 데이터 소스
- 02-2. 주가 데이터 수집
- 02-3. 재무제표 데이터 수집
- 02-4. 결측치·수정주가·상장폐지 처리
