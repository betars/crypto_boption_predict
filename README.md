# Binance hourly crypto direction model

This project models hourly `up/down` probabilities for BTC, ETH, SOL, and XRP using Binance market data. The intended use is Polymarket trading, so the model output is a probability, not just a class label.

## Modeling target

For each asset and hour:

```text
label = 1 if close[t+1h] > close[t]
label = 0 otherwise
```

This assumes the Polymarket market resolves from the Binance price at one hourly boundary to the next. If a specific Polymarket market uses another oracle or timestamp rule, adjust the label before trading.

## Quick start

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt

python scripts/fetch_binance_klines.py --days 365
python scripts/build_features.py
python scripts/train_baseline.py
```

Outputs:

```text
data/raw/binance_1h.csv
data/processed/features_1h.csv
models/baseline_hourly_direction.joblib
```

## Trading framing

At trade time:

```text
edge_yes = p_model_up - polymarket_yes_ask
edge_no = (1 - p_model_up) - polymarket_no_ask
```

Trade only when the edge is large enough to cover spread, slippage, fees, and model error. A first threshold to test is `0.04` to `0.08`.

## Next improvements

- Match each Polymarket hourly market's exact Binance timestamp and resolution rule.
- Add Binance order book, funding, open interest, and liquidation features.
- Add Polymarket bid/ask, spread, volume, and order book imbalance.
- Replace the single holdout split with walk-forward validation.
- Calibrate probabilities and evaluate Brier score, log loss, realized EV, drawdown, and confidence buckets.
# crypto_boption_predict
