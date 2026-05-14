from datetime import timedelta

import pandas as pd
from sklearn.linear_model import LinearRegression
from sklearn.metrics import r2_score


def predict_next_close(frame: pd.DataFrame) -> dict:
    data = frame.copy()
    if len(data) < 35:
        last_close = float(data["close"].iloc[-1]) if not data.empty else 0
        return {
            "predicted_for": None,
            "predicted_close": round(last_close, 2),
            "confidence": 35,
            "model_name": "LinearRegression",
            "features": {},
            "note": "Prediction confidence is limited because fewer than 35 records are available.",
        }

    data["lag_close"] = data["close"].shift(1)
    data["return_lag"] = data["daily_return"].shift(1)
    data["target"] = data["close"].shift(-1)
    feature_cols = ["lag_close", "ma_7", "ma_30", "return_lag", "volume", "volatility"]
    train = data.dropna(subset=feature_cols + ["target"])

    model = LinearRegression()
    x = train[feature_cols]
    y = train["target"]
    model.fit(x, y)
    fitted = model.predict(x)
    r2 = max(0.0, min(1.0, r2_score(y, fitted)))
    latest = data.iloc[-1:][feature_cols].ffill().fillna(0)
    prediction = float(model.predict(latest)[0])
    last_date = pd.to_datetime(data["date"].iloc[-1]).date()
    predicted_for = last_date + timedelta(days=1)
    confidence = int(45 + r2 * 50)
    return {
        "predicted_for": predicted_for.isoformat(),
        "predicted_close": round(prediction, 2),
        "confidence": confidence,
        "model_name": "LinearRegression",
        "features": {col: round(float(latest.iloc[0][col]), 4) for col in feature_cols},
        "note": "Educational forecast based on recent technical features, not financial advice.",
    }
