import pandas as pd


def build_recommendation(symbol: str, frame: pd.DataFrame) -> dict:
    if frame.empty:
        return {
            "action": "HOLD",
            "confidence": 0,
            "insight": f"{symbol} does not have enough data for an AI recommendation yet.",
            "factors": {},
        }
    latest = frame.iloc[-1]
    score = 0
    factors = {
        "trend": "bullish" if latest["close"] >= latest["ma_30"] else "bearish",
        "rsi": round(float(latest["rsi"]), 2),
        "volatility": round(float(latest["volatility"]), 4),
        "macd": round(float(latest["macd"]), 4),
        "drawdown": round(float(latest["drawdown"]), 4),
    }

    score += 2 if latest["close"] > latest["ma_30"] else -2
    score += 1 if latest["ma_7"] > latest["ma_30"] else -1
    score += 1 if latest["macd"] > latest["macd_signal"] else -1
    score += 1 if 45 <= latest["rsi"] <= 68 else -1 if latest["rsi"] > 75 or latest["rsi"] < 30 else 0
    score += 1 if latest["volatility"] < 0.35 else -1
    score += 1 if latest["drawdown"] > -0.12 else -1

    if score >= 3:
        action = "BUY"
    elif score <= -2:
        action = "SELL"
    else:
        action = "HOLD"
    confidence = min(96, max(50, 55 + abs(score) * 7))
    risk = "low" if latest["volatility"] < 0.25 else "moderate" if latest["volatility"] < 0.45 else "elevated"
    insight = (
        f"{symbol} shows {factors['trend']} momentum with {risk} volatility, "
        f"RSI at {factors['rsi']}, and MACD {'above' if latest['macd'] > latest['macd_signal'] else 'below'} signal. "
        f"Suggested action: {action}."
    )
    return {"action": action, "confidence": confidence, "insight": insight, "factors": factors}
