#!/usr/bin/env python3
"""Train a baseline hourly direction probability model."""

from __future__ import annotations

import argparse
from pathlib import Path

import joblib
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingClassifier
from sklearn.metrics import accuracy_score, brier_score_loss, log_loss, roc_auc_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder


TARGET = "label_up_next_1h"
DROP_COLUMNS = {
    TARGET,
    "open_time",
    "close_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "quote_volume",
    "trade_count",
    "taker_buy_base_volume",
    "taker_buy_quote_volume",
}


def time_split(data: pd.DataFrame, test_fraction: float) -> tuple[pd.DataFrame, pd.DataFrame]:
    unique_times = data["open_time"].drop_duplicates().sort_values()
    split_at = unique_times.iloc[int(len(unique_times) * (1 - test_fraction))]
    train = data[data["open_time"] < split_at].copy()
    test = data[data["open_time"] >= split_at].copy()
    return train, test


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--features", default="data/processed/features_1h.csv")
    parser.add_argument("--model-out", default="models/baseline_hourly_direction.joblib")
    parser.add_argument("--test-fraction", type=float, default=0.2)
    args = parser.parse_args()

    data = pd.read_csv(args.features, parse_dates=["open_time", "close_time"])
    data = data.sort_values(["open_time", "symbol"])
    train, test = time_split(data, args.test_fraction)

    feature_columns = [column for column in data.columns if column not in DROP_COLUMNS]
    categorical_columns = ["symbol"]
    numeric_columns = [column for column in feature_columns if column not in categorical_columns]

    preprocessor = ColumnTransformer(
        transformers=[
            ("symbol", OneHotEncoder(handle_unknown="ignore"), categorical_columns),
            ("numeric", "passthrough", numeric_columns),
        ]
    )
    model = Pipeline(
        steps=[
            ("preprocess", preprocessor),
            (
                "classifier",
                HistGradientBoostingClassifier(
                    max_iter=250,
                    learning_rate=0.04,
                    l2_regularization=0.02,
                    random_state=7,
                ),
            ),
        ]
    )

    model.fit(train[feature_columns], train[TARGET])
    probabilities = model.predict_proba(test[feature_columns])[:, 1]
    predictions = (probabilities >= 0.5).astype(int)

    print(f"Train rows: {len(train):,}")
    print(f"Test rows: {len(test):,}")
    print(f"Accuracy: {accuracy_score(test[TARGET], predictions):.4f}")
    print(f"AUC: {roc_auc_score(test[TARGET], probabilities):.4f}")
    print(f"Log loss: {log_loss(test[TARGET], probabilities):.4f}")
    print(f"Brier: {brier_score_loss(test[TARGET], probabilities):.4f}")

    for symbol, symbol_test in test.assign(probability=probabilities).groupby("symbol"):
        print(
            f"{symbol}: "
            f"accuracy={accuracy_score(symbol_test[TARGET], symbol_test['probability'] >= 0.5):.4f}, "
            f"brier={brier_score_loss(symbol_test[TARGET], symbol_test['probability']):.4f}"
        )

    out = Path(args.model_out)
    out.parent.mkdir(parents=True, exist_ok=True)
    joblib.dump({"model": model, "feature_columns": feature_columns}, out)
    print(f"Wrote model to {out}")


if __name__ == "__main__":
    main()
