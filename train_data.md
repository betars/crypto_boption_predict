# Train/Test Data Construction

## Purpose

Construct supervised learning data for per-second prediction of whether the current hourly candle will close up.

The raw data source is Binance 1-second kline data for:

```text
BTCUSDT
ETHUSDT
SOLUSDT
XRPUSDT
```

The model predicts every second:

```text
P(current_hour_close > current_hour_open)
```

## Raw Input

Each raw 1-second kline row should contain at least:

```text
symbol
timestamp
open
high
low
close
volume
quote_volume
trade_count
taker_buy_base_volume
taker_buy_quote_volume
```

Example:

```text
symbol: BTCUSDT
timestamp: 2026-01-01 10:23:17 UTC
open: ...
high: ...
low: ...
close: ...
volume: ...
```

## Hourly Event Fields

For each row, derive:

```text
hour_start = floor(timestamp to hour)
hour_end = hour_start + 1 hour
elapsed_seconds = timestamp - hour_start
remaining_seconds = hour_end - timestamp
```

Example:

```text
timestamp: 10:23:17
hour_start: 10:00:00
hour_end: 11:00:00
elapsed_seconds: 1397
remaining_seconds: 2203
```

## Label Construction

The label is created per `symbol + hour_start`.

Use the 1-second klines inside that hour:

```text
hour_open = first open in the hour
hour_close = last close in the hour
```

Then:

```text
label_up = 1 if hour_close > hour_open else 0
```

Example:

```text
hour_start: 10:00:00
hour_end: 11:00:00
hour_open: open at 10:00:00
hour_close: close at 10:59:59

label_up = 1 if hour_close > hour_open else 0
```

The same `label_up` is attached to every second inside the same `symbol + hour_start` event.

## Per-second Feature Construction

Each row is one training sample.

At timestamp `t`, features must use only information available at or before `t`.

Recommended per-second features:

```text
symbol
timestamp
hour_start
elapsed_seconds
remaining_seconds
hour_of_day
day_of_week
close
hour_open
current_return_from_hour_open
return_1s
return_5s
return_15s
return_30s
return_60s
return_300s
rolling_volatility_30s
rolling_volatility_60s
rolling_volatility_300s
rolling_volume_10s
rolling_volume_60s
rolling_quote_volume_60s
taker_buy_ratio_10s
taker_buy_ratio_60s
high_so_far
low_so_far
distance_to_high_so_far
distance_to_low_so_far
label_up
```

Definitions:

```text
current_return_from_hour_open = close[t] / hour_open - 1
return_1s = close[t] / close[t-1s] - 1
return_5s = close[t] / close[t-5s] - 1
return_60s = close[t] / close[t-60s] - 1
rolling_volatility_60s = std(return_1s over the past 60 seconds)
rolling_volume_60s = sum(volume over the past 60 seconds)
high_so_far = max(high from hour_start through t)
low_so_far = min(low from hour_start through t)
distance_to_high_so_far = close[t] / high_so_far - 1
distance_to_low_so_far = close[t] / low_so_far - 1
```

## Cross-asset Features

Because BTC, ETH, SOL, and XRP are correlated, add cross-asset state at the same timestamp.

Useful cross-asset features:

```text
BTC_current_return_from_hour_open
ETH_current_return_from_hour_open
SOL_current_return_from_hour_open
XRP_current_return_from_hour_open
BTC_return_60s
ETH_return_60s
SOL_return_60s
XRP_return_60s
market_average_return_from_hour_open
symbol_relative_strength_vs_BTC
```

These features must also be computed using only data available at or before the current timestamp.

## Leakage Rules

Do not use future information.

Invalid features:

```text
future seconds inside the same hour
final hourly close
final hourly high
final hourly low
future rolling windows
any feature computed with centered windows
```

Invalid splitting:

```text
random train/test split by second-level rows
```

This leaks information because rows from the same hourly event share the same label.

Valid features:

```text
prices observed up to current second t
volume observed up to current second t
high/low observed so far in the current hour
previous hours' complete candles
rolling windows ending at t
```

## Train/Validation/Test Split

Split by hourly event, not by row.

The split key should be:

```text
hour_start
```

or stricter:

```text
global hour_start shared across all symbols
```

Recommended approach:

```text
All symbols for the same hour_start go into the same split.
```

Example:

```text
Train: earlier 70% of hours
Validation: next 15% of hours
Test: latest 15% of hours
```

Concrete date example:

```text
Train: 2024-01-01 through 2025-06-30
Validation: 2025-07-01 through 2025-12-31
Test: 2026-01-01 onward
```

This prevents the same hourly event from appearing in multiple splits.

## Optional Sampling

Full 1-second data is large.

Approximate size:

```text
1 symbol, 1 day: 86,400 rows
4 symbols, 1 day: 345,600 rows
4 symbols, 1 year: about 126 million rows
```

For early experiments, sample the per-second rows.

Options:

```text
every 5 seconds
every 10 seconds
selected elapsed_seconds checkpoints
```

Useful checkpoints:

```text
5
10
30
60
120
300
600
900
1800
2700
3300
3540
```

Sampling must be applied after labels and leakage-safe features are constructed.

## Final Training Table

The final table should look like:

```text
symbol
timestamp
hour_start
elapsed_seconds
remaining_seconds
hour_of_day
day_of_week
close
hour_open
current_return_from_hour_open
return_1s
return_5s
return_15s
return_30s
return_60s
return_300s
rolling_volatility_30s
rolling_volatility_60s
rolling_volatility_300s
rolling_volume_10s
rolling_volume_60s
rolling_quote_volume_60s
taker_buy_ratio_10s
taker_buy_ratio_60s
high_so_far
low_so_far
distance_to_high_so_far
distance_to_low_so_far
cross_asset_features...
label_up
split
```

## Minimal Pseudocode

```python
df["timestamp"] = pd.to_datetime(df["timestamp"], utc=True)
df["hour_start"] = df["timestamp"].dt.floor("h")
df["hour_end"] = df["hour_start"] + pd.Timedelta(hours=1)

hour_info = (
    df.groupby(["symbol", "hour_start"])
      .agg(
          hour_open=("open", "first"),
          hour_close=("close", "last"),
      )
      .reset_index()
)

hour_info["label_up"] = (
    hour_info["hour_close"] > hour_info["hour_open"]
).astype(int)

df = df.merge(hour_info, on=["symbol", "hour_start"], how="left")

df["elapsed_seconds"] = (
    df["timestamp"] - df["hour_start"]
).dt.total_seconds().astype(int)

df["remaining_seconds"] = 3600 - df["elapsed_seconds"]

df["current_return_from_hour_open"] = (
    df["close"] / df["hour_open"] - 1
)

df["return_1s"] = df.groupby("symbol")["close"].pct_change(1)
df["return_5s"] = df.groupby("symbol")["close"].pct_change(5)
df["return_60s"] = df.groupby("symbol")["close"].pct_change(60)

df["rolling_volatility_60s"] = (
    df.groupby("symbol")["return_1s"]
      .rolling(60)
      .std()
      .reset_index(level=0, drop=True)
)

df["rolling_volume_60s"] = (
    df.groupby("symbol")["volume"]
      .rolling(60)
      .sum()
      .reset_index(level=0, drop=True)
)

df["high_so_far"] = (
    df.groupby(["symbol", "hour_start"])["high"].cummax()
)

df["low_so_far"] = (
    df.groupby(["symbol", "hour_start"])["low"].cummin()
)

df["distance_to_high_so_far"] = df["close"] / df["high_so_far"] - 1
df["distance_to_low_so_far"] = df["close"] / df["low_so_far"] - 1
```

## Summary

The correct construction order is:

```text
1. Load Binance 1-second kline data.
2. Assign each row to an hourly event.
3. Build one label per symbol + hour_start.
4. Attach that label to every second in the hour.
5. Build leakage-safe per-second features.
6. Add cross-asset features.
7. Split by hour_start into train/validation/test.
8. Optionally sample rows for faster experiments.
```

