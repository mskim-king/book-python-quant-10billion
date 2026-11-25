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
