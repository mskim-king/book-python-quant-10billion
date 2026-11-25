"""책 예제용 가상 주가 데이터를 만듭니다. (실제 종목 데이터가 아닙니다)"""
import numpy as np
import pandas as pd


def make_prices(days: int = 756, seed: int = 42) -> pd.DataFrame:
    """영업일 기준 약 3년치 가상 종가 (종목 A, B, C)."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2023-01-02", periods=days)
    # 종목별 연 기대수익률·변동성 (가정)
    params = {"A": (0.10, 0.25), "B": (0.06, 0.15), "C": (0.14, 0.40)}
    data = {}
    for name, (mu, vol) in params.items():
        daily = rng.normal(mu / 252, vol / np.sqrt(252), days)
        data[name] = 10_000 * np.exp(np.cumsum(daily))
    return pd.DataFrame(data, index=dates).round(0)


def make_universe(n: int = 40, months: int = 72, seed: int = 7):
    """팩터 실습용 가상 종목 n개의 월말 가격과 재무지표.

    가정(실제 시장 아님): 저PBR·고ROE·저변동성 종목에 작은 초과수익을 주고,
    종목별 '추세'가 천천히 바뀌도록 만들어 모멘텀이 나타나게 했습니다.
    """
    rng = np.random.default_rng(seed)
    names = [f"S{i:02d}" for i in range(1, n + 1)]
    dates = pd.date_range("2020-01-31", periods=months, freq="ME")
    pbr = np.round(rng.lognormal(0.0, 0.5, n), 2)              # 주가순자산비율
    per = np.round(np.clip(pbr * rng.uniform(6, 14, n), 3, 60), 1)
    roe = np.round(rng.normal(0.10, 0.06, n), 3)               # 자기자본이익률
    debt = np.round(rng.uniform(0.2, 2.5, n), 2)               # 부채비율(배)
    vol = rng.uniform(0.15, 0.55, n)                           # 연 변동성
    value_z = -(np.log(pbr) - np.log(pbr).mean()) / np.log(pbr).std()
    qual_z = (roe - roe.mean()) / roe.std()
    lowv_z = -(vol - vol.mean()) / vol.std()
    premium = 0.0015 * value_z + 0.0012 * qual_z + 0.0010 * lowv_z   # 월 초과수익(가정)
    market = rng.normal(0.006, 0.045, months)
    trend = np.zeros(n)
    rets = np.zeros((months, n))
    for t in range(months):
        trend = 0.9 * trend + rng.normal(0, 0.004, n)           # 천천히 바뀌는 추세 → 모멘텀
        rets[t] = market[t] + premium + trend + rng.normal(0, vol / np.sqrt(12))
    prices = pd.DataFrame(10_000 * np.cumprod(1 + rets, axis=0), index=dates, columns=names).round(0)
    fundamentals = pd.DataFrame({"PBR": pbr, "PER": per, "ROE": roe, "부채비율": debt}, index=names)
    return prices, fundamentals


def make_pair(days: int = 504, seed: int = 11) -> pd.DataFrame:
    """함께 움직이는(공적분) 가상 종목 X, Y 의 종가."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2024-01-02", periods=days)
    x = 100 * np.exp(np.cumsum(rng.normal(0.0002, 0.015, days)))
    spread = np.zeros(days)
    for t in range(1, days):
        spread[t] = 0.95 * spread[t - 1] + rng.normal(0, 0.8)   # 평균으로 돌아오는 차이
    y = 1.5 * x + 20 + spread
    return pd.DataFrame({"X": x, "Y": y}, index=dates).round(2)


def make_assets(days: int = 1260, seed: int = 21) -> pd.DataFrame:
    """자산배분 실습용 가상 자산(주식·채권·금) 약 5년치 종가."""
    rng = np.random.default_rng(seed)
    dates = pd.bdate_range("2021-01-04", periods=days)
    cov = np.array([[0.18**2, -0.2 * 0.18 * 0.06, 0.1 * 0.18 * 0.15],
                    [-0.2 * 0.18 * 0.06, 0.06**2, 0.2 * 0.06 * 0.15],
                    [0.1 * 0.18 * 0.15, 0.2 * 0.06 * 0.15, 0.15**2]]) / 252
    mu = np.array([0.07, 0.03, 0.04]) / 252
    r = rng.multivariate_normal(mu, cov, days)
    return pd.DataFrame(100 * np.exp(np.cumsum(r, axis=0)), index=dates, columns=["주식", "채권", "금"]).round(2)
