#!/usr/bin/env python3
"""Fetch hourly Binance spot klines for the target assets."""

from __future__ import annotations

import argparse
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pandas as pd
import requests


BINANCE_KLINES_URL = "https://api.binance.com/api/v3/klines"
DEFAULT_SYMBOLS = ["BTCUSDT", "ETHUSDT", "SOLUSDT", "XRPUSDT"]


def to_millis(dt: datetime) -> int:
    return int(dt.timestamp() * 1000)


def fetch_symbol(symbol: str, start_ms: int, end_ms: int, interval: str) -> pd.DataFrame:
    rows = []
    cursor = start_ms

    while cursor < end_ms:
        response = requests.get(
            BINANCE_KLINES_URL,
            params={
                "symbol": symbol,
                "interval": interval,
                "startTime": cursor,
                "endTime": end_ms,
                "limit": 1000,
            },
            timeout=30,
        )
        response.raise_for_status()
        batch = response.json()
        if not batch:
            break

        rows.extend(batch)
        next_cursor = int(batch[-1][6]) + 1
        if next_cursor <= cursor:
            break
        cursor = next_cursor
        time.sleep(0.15)

    columns = [
        "open_time",
        "open",
        "high",
        "low",
        "close",
        "volume",
        "close_time",
        "quote_volume",
        "trade_count",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
        "ignore",
    ]
    frame = pd.DataFrame(rows, columns=columns)
    if frame.empty:
        return frame

    numeric_columns = [
        "open",
        "high",
        "low",
        "close",
        "volume",
        "quote_volume",
        "taker_buy_base_volume",
        "taker_buy_quote_volume",
    ]
    frame[numeric_columns] = frame[numeric_columns].astype(float)
    frame["trade_count"] = frame["trade_count"].astype(int)
    frame["open_time"] = pd.to_datetime(frame["open_time"], unit="ms", utc=True)
    frame["close_time"] = pd.to_datetime(frame["close_time"], unit="ms", utc=True)
    frame["symbol"] = symbol
    return frame.drop(columns=["ignore"])


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--symbols", nargs="+", default=DEFAULT_SYMBOLS)
    parser.add_argument("--interval", default="1h")
    parser.add_argument("--days", type=int, default=365)
    parser.add_argument("--out", default="data/raw/binance_1h.csv")
    args = parser.parse_args()

    end = datetime.now(timezone.utc).replace(minute=0, second=0, microsecond=0)
    start = end - timedelta(days=args.days)

    frames = [
        fetch_symbol(symbol, to_millis(start), to_millis(end), args.interval)
        for symbol in args.symbols
    ]
    data = pd.concat([frame for frame in frames if not frame.empty], ignore_index=True)
    data = data.sort_values(["symbol", "open_time"]).drop_duplicates(["symbol", "open_time"])

    out = Path(args.out)
    out.parent.mkdir(parents=True, exist_ok=True)
    data.to_csv(out, index=False)
    print(f"Wrote {len(data):,} rows to {out}")


if __name__ == "__main__":
    main()
