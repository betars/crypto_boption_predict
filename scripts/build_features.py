#!/usr/bin/env python3
"""Build leakage-safe hourly features from Binance klines."""

from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np
import pandas as pd


def add_symbol_features(group: pd.DataFrame) -> pd.DataFrame:
    group = group.sort_values("open_time").copy()

    group["ret_1h"] = group["close"].pct_change()
    group["ret_3h"] = group["close"].pct_change(3)
    group["ret_6h"] = group["close"].pct_change(6)
    group["ret_12h"] = group["close"].pct_change(12)
    group["ret_24h"] = group["close"].pct_change(24)
    group["range_pct"] = (group["high"] - group["low"]) / group["open"]
    group["body_pct"] = (group["close"] - group["open"]) / group["open"]
    group["upper_wick_pct"] = (group["high"] - np.maximum(group["open"], group["close"])) / group["open"]
    group["lower_wick_pct"] = (np.minimum(group["open"], group["close"]) - group["low"]) / group["open"]

    for window in [6, 12, 24]:
        group[f"volatility_{window}h"] = group["ret_1h"].rolling(window).std()
        volume_mean = group["quote_volume"].rolling(window).mean()
        volume_std = group["quote_volume"].rolling(window).std()
        group[f"quote_volume_z_{window}h"] = (group["quote_volume"] - volume_mean) / volume_std

    group["taker_buy_ratio"] = group["taker_buy_quote_volume"] / group["quote_volume"].replace(0, np.nan)
    group["next_close"] = group["close"].shift(-1)
    group["label_up_next_1h"] = (group["next_close"] > group["close"]).astype(int)
    return group


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--infile", default="data/raw/binance_1h.csv")
    parser.add_argument("--out", default="data/processed/features_1h.csv")
    args = parser.parse_args()

    data = pd.read_csv(args.infile, parse_dates=["open_time", "close_time"])
    data = data.sort_values(["symbol", "open_time"])
    featured = data.groupby("symbol", group_keys=False).apply(add_symbol_features)

    cross_returns = (
        featured.pivot(index="open_time", columns="symbol", values="ret_1h")
        .add_prefix("market_ret_1h_")
        .reset_index()
    )
    featured = featured.merge(cross_returns, on="open_time", how="left")
    featured["hour_utc"] = featured["open_time"].dt.hour
    featured["day_of_week"] = featured["open_time"].dt.dayofweek

    featured = featured.dropna().drop(columns=["next_close"])
    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    featured.to_csv(out, index=False)
    print(f"Wrote {len(featured):,} rows to {out}")


if __name__ == "__main__":
    main()
