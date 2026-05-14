from datetime import date

import numpy as np
import pandas as pd
import yfinance as yf
from fastapi import HTTPException
from sqlalchemy.orm import Session

from app.core.config import get_settings
from app.core.symbols import normalize_symbol
from app.models.entities import Company, StockPrice, TechnicalIndicator
from app.services.cache import TTLCache


settings = get_settings()
market_cache = TTLCache(settings.cache_ttl_seconds)


def get_company_or_404(db: Session, symbol: str) -> Company:
    normalized = normalize_symbol(symbol)
    company = db.query(Company).filter(Company.symbol == normalized).one_or_none()
    if not company:
        raise HTTPException(status_code=404, detail=f"Unsupported stock symbol: {symbol}")
    return company


def fetch_market_data(symbol: str, period: str = "1y") -> pd.DataFrame:
    key = f"yf:{symbol}:{period}"
    cached = market_cache.get(key)
    if cached is not None:
        return cached.copy()

    frame = yf.download(symbol, period=period, interval="1d", auto_adjust=False, progress=False)
    if frame.empty:
        raise HTTPException(status_code=502, detail=f"No market data returned for {symbol}")

    if isinstance(frame.columns, pd.MultiIndex):
        frame.columns = [col[0] for col in frame.columns]

    frame = frame.reset_index()
    frame = frame.rename(
        columns={
            "Date": "date",
            "Open": "open",
            "High": "high",
            "Low": "low",
            "Close": "close",
            "Volume": "volume",
        }
    )
    cleaned = clean_market_data(frame)
    market_cache.set(key, cleaned)
    return cleaned.copy()


def clean_market_data(frame: pd.DataFrame) -> pd.DataFrame:
    required = ["date", "open", "high", "low", "close", "volume"]
    missing = [column for column in required if column not in frame.columns]
    if missing:
        raise HTTPException(status_code=422, detail=f"Missing market columns: {', '.join(missing)}")

    cleaned = frame[required].copy()
    cleaned["date"] = pd.to_datetime(cleaned["date"], errors="coerce").dt.date
    for column in ["open", "high", "low", "close", "volume"]:
        cleaned[column] = pd.to_numeric(cleaned[column], errors="coerce")
    cleaned = cleaned.dropna(subset=required)
    cleaned = cleaned[cleaned["volume"] >= 0]
    cleaned = cleaned.drop_duplicates(subset=["date"]).sort_values("date")
    return cleaned.reset_index(drop=True)


def upsert_prices(db: Session, company: Company, frame: pd.DataFrame) -> int:
    existing = {
        row.date: row
        for row in db.query(StockPrice).filter(StockPrice.company_id == company.id).all()
    }
    count = 0
    for row in frame.to_dict(orient="records"):
        price_date: date = row["date"]
        stock = existing.get(price_date)
        payload = {
            "open": float(row["open"]),
            "high": float(row["high"]),
            "low": float(row["low"]),
            "close": float(row["close"]),
            "volume": int(row["volume"]),
        }
        if stock:
            for key, value in payload.items():
                setattr(stock, key, value)
        else:
            db.add(StockPrice(company_id=company.id, date=price_date, **payload))
        count += 1
    db.commit()
    return count


def load_prices(db: Session, company: Company, limit: int | None = None) -> pd.DataFrame:
    query = db.query(StockPrice).filter(StockPrice.company_id == company.id).order_by(StockPrice.date)
    rows = query.all()
    if not rows:
        return pd.DataFrame(columns=["date", "open", "high", "low", "close", "volume"])
    frame = pd.DataFrame(
        [
            {
                "date": row.date,
                "open": row.open,
                "high": row.high,
                "low": row.low,
                "close": row.close,
                "volume": row.volume,
            }
            for row in rows
        ]
    )
    if limit:
        frame = frame.tail(limit)
    return frame.reset_index(drop=True)


def ensure_prices(db: Session, company: Company) -> pd.DataFrame:
    frame = load_prices(db, company)
    if frame.empty:
        frame = fetch_market_data(company.symbol, settings.default_history_period)
        upsert_prices(db, company, frame)
    return frame


def enrich_metrics(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    if data.empty:
        return data
    data["daily_return"] = (data["close"] - data["open"]) / data["open"]
    data["cumulative_return"] = (1 + data["daily_return"]).cumprod() - 1
    data["ma_7"] = data["close"].rolling(7, min_periods=1).mean()
    data["ma_30"] = data["close"].rolling(30, min_periods=1).mean()
    data["high_52w"] = data["high"].rolling(252, min_periods=1).max()
    data["low_52w"] = data["low"].rolling(252, min_periods=1).min()
    data["volatility"] = data["daily_return"].rolling(30, min_periods=2).std().fillna(0) * np.sqrt(252)
    data["average_volume"] = data["volume"].rolling(30, min_periods=1).mean()
    data["relative_volume"] = data["volume"] / data["average_volume"].replace(0, np.nan)
    data["drawdown"] = data["close"] / data["close"].cummax() - 1
    return data.replace([np.inf, -np.inf], np.nan).fillna(0)


def calculate_indicators(frame: pd.DataFrame) -> pd.DataFrame:
    data = enrich_metrics(frame)
    if data.empty:
        return data
    close = data["close"]
    delta = close.diff()
    gain = delta.clip(lower=0).rolling(14, min_periods=1).mean()
    loss = (-delta.clip(upper=0)).rolling(14, min_periods=1).mean()
    rs = gain / loss.replace(0, np.nan)
    data["rsi"] = (100 - (100 / (1 + rs))).fillna(50)
    ema_12 = close.ewm(span=12, adjust=False).mean()
    ema_26 = close.ewm(span=26, adjust=False).mean()
    data["macd"] = ema_12 - ema_26
    data["macd_signal"] = data["macd"].ewm(span=9, adjust=False).mean()
    data["sma"] = close.rolling(20, min_periods=1).mean()
    data["ema"] = close.ewm(span=20, adjust=False).mean()
    rolling_std = close.rolling(20, min_periods=1).std().fillna(0)
    data["bollinger_middle"] = data["sma"]
    data["bollinger_upper"] = data["sma"] + 2 * rolling_std
    data["bollinger_lower"] = data["sma"] - 2 * rolling_std
    return data.replace([np.inf, -np.inf], np.nan).fillna(0)


def upsert_indicators(db: Session, company: Company, frame: pd.DataFrame) -> None:
    data = calculate_indicators(frame)
    existing = {
        row.date: row
        for row in db.query(TechnicalIndicator).filter(TechnicalIndicator.company_id == company.id).all()
    }
    fields = [
        "rsi",
        "macd",
        "macd_signal",
        "bollinger_upper",
        "bollinger_middle",
        "bollinger_lower",
        "ema",
        "sma",
    ]
    for row in data.to_dict(orient="records"):
        indicator = existing.get(row["date"])
        payload = {field: float(row[field]) for field in fields}
        if indicator:
            for key, value in payload.items():
                setattr(indicator, key, value)
        else:
            db.add(TechnicalIndicator(company_id=company.id, date=row["date"], **payload))
    db.commit()


def range_to_limit(range_value: str) -> int:
    return {"7D": 7, "30D": 30, "90D": 90, "1Y": 252}.get(range_value.upper(), 30)


def to_records(frame: pd.DataFrame) -> list[dict]:
    records = []
    for row in frame.to_dict(orient="records"):
        records.append(
            {
                key: (value.isoformat() if hasattr(value, "isoformat") else round(float(value), 4) if isinstance(value, float) else value)
                for key, value in row.items()
            }
        )
    return records
