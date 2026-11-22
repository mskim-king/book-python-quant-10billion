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
