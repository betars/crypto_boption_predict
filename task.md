# Task: Per-second hourly direction probability forecasting

## Goal

Build a prediction system for BTC, ETH, SOL, and XRP using Binance 1-second kline data.

At every second, the system predicts the probability that the current hourly candle will close up at the next full hour.

The project is prediction-only. It does not include trading, execution, or Polymarket integration.

## Assets

Use Binance spot symbols:

```text
BTCUSDT
ETHUSDT
SOLUSDT
XRPUSDT
```

## Data

Input data is Binance 1-second kline data.

Each row should contain at least:

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

## Prediction Time

For each symbol and each second `t`, generate one prediction using only data available at or before `t`.

Example:

```text
current time: 10:23:17
hour_start: 10:00:00
hour_end: 11:00:00
```

At `10:23:17`, the model predicts whether the `10:00:00-11:00:00` hourly candle will close up.

## Target Definition

The target is whether the current hourly candle closes above its hourly open.

```text
y(t) = 1 if price_at_hour_end > price_at_hour_start
y(t) = 0 otherwise
```

For example:

```text
hour_start = 10:00:00
hour_end = 11:00:00

hour_open = price at 10:00:00
hour_close = price at 11:00:00

y = 1 if hour_close > hour_open else 0
```

Every second inside the same hour has the same final label, but different available information.

## Model Output

The model should output a probability:

```text
P(hour_close > hour_open | data available up to t)
```

Example output:

```text
timestamp: 10:23:17
symbol: BTCUSDT
prob_up: 0.573
```

The main output is probability, not only a hard `up/down` class.

## Core Features

The model should know both the current market state and how much time remains before the next full hour.

Important feature groups:

```text
symbol
elapsed_seconds
remaining_seconds
hour_of_day
day_of_week
current_return_from_hour_open
current_price_distance_to_hour_open
return_1s
return_5s
return_15s
return_30s
return_60s
return_300s
realized_volatility_30s
realized_volatility_60s
realized_volatility_300s
rolling_volume_10s
rolling_volume_60s
rolling_quote_volume_60s
taker_buy_ratio_10s
taker_buy_ratio_60s
high_since_hour_start
low_since_hour_start
distance_to_intrahour_high
distance_to_intrahour_low
```

Cross-asset features are also useful:

```text
BTC current_return_from_hour_open
ETH current_return_from_hour_open
SOL current_return_from_hour_open
XRP current_return_from_hour_open
market_average_return_from_hour_open
symbol_relative_strength_vs_BTC
```

## Recommended Modeling Framing

This is an event countdown probability problem:

```text
At second t inside an hourly event,
estimate the conditional probability that the event resolves up.
```

The difficulty changes as the hour progresses:

```text
00:00:05 into the hour: hard
00:30:00 into the hour: medium
00:59:50 into the hour: much easier
```

Therefore `elapsed_seconds` and `remaining_seconds` are required features.

## Baseline Models

Start simple:

```text
Logistic Regression baseline
Gradient-boosted tree model as the main baseline
```

Possible tree models:

```text
LightGBM
XGBoost
CatBoost
sklearn HistGradientBoostingClassifier
```

A first version can use one global multi-asset model:

```text
input: symbol + per-second features + cross-asset features
output: P(up)
```

Asset-specific models can be compared later.

## Validation

Use time-based validation only.

Do not randomly split rows, because rows inside the same hour are highly correlated.

Recommended split:

```text
Train: earlier hours
Validation: later hours
Test: latest hours
```

Even better:

```text
Walk-forward validation by hour
```

## Evaluation

Evaluate probability quality, not just classification accuracy.

Primary metrics:

```text
Log loss
Brier score
AUC
Accuracy
Calibration curve
```

Evaluate separately by remaining-time bucket:

```text
0-60 seconds remaining
1-5 minutes remaining
5-15 minutes remaining
15-30 minutes remaining
30-60 minutes remaining
```

For each bucket, inspect:

```text
sample count
accuracy
AUC
log loss
Brier score
calibration
```

## Leakage Rules

At prediction time `t`, features must use only information available at or before `t`.

Invalid examples:

```text
using future seconds inside the same hour
using the final hourly close as a feature
using rolling windows that accidentally look forward
random train/test split across rows from the same hour
```

Valid examples:

```text
using prices up to current second t
using volume up to current second t
using high/low observed so far in the current hour
using previous hours' full candles
```

## Final Problem Statement

Build a multi-asset, per-second probability forecasting model using Binance 1-second kline data.

For each asset and each second `t`, predict:

```text
P(current_hour_close > current_hour_open)
```

using only market data available up to `t`.

