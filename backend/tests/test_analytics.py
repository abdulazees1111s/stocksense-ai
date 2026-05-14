from datetime import date, timedelta

import pandas as pd

from app.services.data_service import calculate_indicators, clean_market_data, enrich_metrics
from app.services.recommendation import build_recommendation
from app.ml.predictor import predict_next_close


def sample_frame(rows: int = 80) -> pd.DataFrame:
    start = date(2025, 1, 1)
    return pd.DataFrame(
        {
            "date": [start + timedelta(days=i) for i in range(rows)],
            "open": [100 + i * 0.8 for i in range(rows)],
            "high": [104 + i * 0.8 for i in range(rows)],
            "low": [98 + i * 0.8 for i in range(rows)],
            "close": [101 + i for i in range(rows)],
            "volume": [1_000_000 + i * 1000 for i in range(rows)],
        }
    )


def test_clean_market_data_sorts_and_deduplicates():
    raw = pd.DataFrame(
        [
            {"date": "2025-01-02", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10},
            {"date": "2025-01-01", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10},
            {"date": "2025-01-01", "open": 1, "high": 2, "low": 1, "close": 2, "volume": 10},
        ]
    )
    cleaned = clean_market_data(raw)
    assert len(cleaned) == 2
    assert cleaned.iloc[0]["date"].isoformat() == "2025-01-01"


def test_enrich_metrics_adds_required_columns():
    enriched = enrich_metrics(sample_frame())
    for column in ["daily_return", "ma_7", "ma_30", "high_52w", "low_52w", "volatility", "drawdown"]:
        assert column in enriched.columns


def test_indicators_and_recommendation_are_valid():
    indicators = calculate_indicators(sample_frame())
    assert {"rsi", "macd", "bollinger_upper", "ema", "sma"}.issubset(indicators.columns)
    recommendation = build_recommendation("TCS", indicators)
    assert recommendation["action"] in {"BUY", "HOLD", "SELL"}
    assert recommendation["confidence"] >= 50


def test_prediction_returns_price_and_confidence():
    prediction = predict_next_close(calculate_indicators(sample_frame()))
    assert prediction["predicted_close"] > 0
    assert 0 <= prediction["confidence"] <= 100
