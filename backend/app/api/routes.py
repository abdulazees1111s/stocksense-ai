from datetime import UTC, date, datetime
from io import BytesIO, StringIO

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session

from app.db.session import get_db
from app.models.entities import Company, PortfolioHolding, Prediction, SentimentSnapshot, WatchlistItem
from app.ml.predictor import predict_next_close
from app.services.data_service import (
    calculate_indicators,
    ensure_prices,
    enrich_metrics,
    fetch_market_data,
    get_company_or_404,
    range_to_limit,
    to_records,
    upsert_indicators,
    upsert_prices,
)
from app.services.recommendation import build_recommendation
from app.services.sentiment import analyze_sentiment


router = APIRouter()


def envelope(data, meta: dict | None = None, symbol: str | None = None) -> dict:
    payload = {"data": data, "generated_at": datetime.now(UTC).isoformat()}
    if symbol:
        payload["symbol"] = symbol
    if meta:
        payload["meta"] = meta
    return payload


@router.get("/health")
def health() -> dict:
    return envelope({"status": "ok", "service": "StockSense AI Pro"})


@router.get("/companies")
def companies(db: Session = Depends(get_db)) -> dict:
    rows = db.query(Company).order_by(Company.display_symbol).all()
    return envelope(
        [
            {
                "symbol": row.display_symbol,
                "yahoo_symbol": row.symbol,
                "name": row.name,
                "sector": row.sector,
                "exchange": row.exchange,
            }
            for row in rows
        ]
    )


@router.post("/ingest")
def ingest_all(db: Session = Depends(get_db)) -> dict:
    results = []
    for company in db.query(Company).all():
        frame = fetch_market_data(company.symbol)
        count = upsert_prices(db, company, frame)
        upsert_indicators(db, company, frame)
        results.append({"symbol": company.display_symbol, "rows": count})
    return envelope(results, meta={"message": "Market data refreshed"})


@router.post("/ingest/{symbol}")
def ingest_symbol(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    frame = fetch_market_data(company.symbol)
    count = upsert_prices(db, company, frame)
    upsert_indicators(db, company, frame)
    return envelope({"rows": count}, symbol=company.display_symbol)


@router.get("/data/{symbol}")
def stock_data(symbol: str, range: str = "30D", db: Session = Depends(get_db)) -> dict:  # noqa: A002
    company = get_company_or_404(db, symbol)
    frame = calculate_indicators(ensure_prices(db, company)).tail(range_to_limit(range))
    return envelope(to_records(frame), symbol=company.display_symbol, meta={"range": range.upper()})


@router.get("/summary/{symbol}")
def summary(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    frame = enrich_metrics(ensure_prices(db, company))
    if frame.empty:
        raise HTTPException(status_code=404, detail="No price data available")
    latest = frame.iloc[-1]
    data = {
        "latest_close": round(float(latest["close"]), 2),
        "average_close": round(float(frame["close"].mean()), 2),
        "high_52w": round(float(frame["high"].tail(252).max()), 2),
        "low_52w": round(float(frame["low"].tail(252).min()), 2),
        "volatility": round(float(latest["volatility"]), 4),
        "average_volume": int(frame["volume"].tail(30).mean()),
        "daily_return": round(float(latest["daily_return"]), 4),
        "cumulative_return": round(float(latest["cumulative_return"]), 4),
        "drawdown": round(float(latest["drawdown"]), 4),
    }
    return envelope(data, symbol=company.display_symbol)


@router.get("/indicators/{symbol}")
def indicators(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    frame = calculate_indicators(ensure_prices(db, company)).tail(60)
    fields = ["date", "rsi", "macd", "macd_signal", "bollinger_upper", "bollinger_middle", "bollinger_lower", "ema", "sma"]
    return envelope(to_records(frame[fields]), symbol=company.display_symbol)


@router.get("/recommendation/{symbol}")
def recommendation(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    frame = calculate_indicators(ensure_prices(db, company))
    return envelope(build_recommendation(company.display_symbol, frame), symbol=company.display_symbol)


@router.get("/predict/{symbol}")
def prediction(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    frame = calculate_indicators(ensure_prices(db, company))
    result = predict_next_close(frame)
    if result.get("predicted_for"):
        db.add(
            Prediction(
                company_id=company.id,
                predicted_for=date.fromisoformat(result["predicted_for"]),
                predicted_close=result["predicted_close"],
                confidence=result["confidence"],
                model_name=result["model_name"],
            )
        )
        db.commit()
    return envelope(result, symbol=company.display_symbol)


@router.get("/sentiment/{symbol}")
def sentiment(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    result = analyze_sentiment(company.symbol)
    db.add(
        SentimentSnapshot(
            company_id=company.id,
            positive=result["positive"],
            neutral=result["neutral"],
            negative=result["negative"],
            compound=result["compound"],
            summary=result["summary"],
        )
    )
    db.commit()
    return envelope(result, symbol=company.display_symbol)


@router.get("/compare")
def compare(symbol1: str, symbol2: str, db: Session = Depends(get_db)) -> dict:
    first = get_company_or_404(db, symbol1)
    second = get_company_or_404(db, symbol2)
    first_frame = calculate_indicators(ensure_prices(db, first))
    second_frame = calculate_indicators(ensure_prices(db, second))
    def stats(company: Company, frame):
        latest = frame.iloc[-1]
        return {
            "symbol": company.display_symbol,
            "latest_close": round(float(latest["close"]), 2),
            "return_30d": round(float(frame["close"].pct_change(30).iloc[-1] if len(frame) > 30 else frame["daily_return"].sum()), 4),
            "volatility": round(float(latest["volatility"]), 4),
            "recommendation": build_recommendation(company.display_symbol, frame)["action"],
        }
    return envelope({"stocks": [stats(first, first_frame), stats(second, second_frame)]})


@router.get("/market/overview")
def market_overview(db: Session = Depends(get_db)) -> dict:
    cards = []
    for company in db.query(Company).order_by(Company.display_symbol).all():
        frame = calculate_indicators(ensure_prices(db, company))
        latest = frame.iloc[-1]
        cards.append(
            {
                "symbol": company.display_symbol,
                "name": company.name,
                "sector": company.sector,
                "close": round(float(latest["close"]), 2),
                "change": round(float(latest["daily_return"]), 4),
                "volatility": round(float(latest["volatility"]), 4),
                "recommendation": build_recommendation(company.display_symbol, frame)["action"],
            }
        )
    return envelope(cards)


@router.get("/market/heatmap")
def market_heatmap(db: Session = Depends(get_db)) -> dict:
    items = []
    for company in db.query(Company).order_by(Company.display_symbol).all():
        frame = enrich_metrics(ensure_prices(db, company))
        latest = frame.iloc[-1]
        items.append(
            {
                "symbol": company.display_symbol,
                "sector": company.sector,
                "change": round(float(latest["daily_return"]), 4),
                "market_value": round(float(latest["close"] * latest["volume"]), 2),
            }
        )
    return envelope(items)


@router.get("/watchlist")
def watchlist(db: Session = Depends(get_db)) -> dict:
    rows = db.query(WatchlistItem, Company).join(Company, Company.id == WatchlistItem.company_id).all()
    return envelope([{"id": item.id, "symbol": company.display_symbol, "name": company.name} for item, company in rows])


@router.post("/watchlist/{symbol}")
def add_watchlist(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    exists = db.query(WatchlistItem).filter(WatchlistItem.company_id == company.id).one_or_none()
    if not exists:
        db.add(WatchlistItem(company_id=company.id))
        db.commit()
    return envelope({"symbol": company.display_symbol, "saved": True})


@router.delete("/watchlist/{symbol}")
def delete_watchlist(symbol: str, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    item = db.query(WatchlistItem).filter(WatchlistItem.company_id == company.id).one_or_none()
    if item:
        db.delete(item)
        db.commit()
    return envelope({"symbol": company.display_symbol, "saved": False})


@router.get("/portfolio")
def portfolio(db: Session = Depends(get_db)) -> dict:
    holdings = db.query(PortfolioHolding).all()
    rows = []
    invested_total = 0.0
    current_total = 0.0
    weighted_risk = 0.0
    for holding in holdings:
        company = db.get(Company, holding.company_id)
        frame = enrich_metrics(ensure_prices(db, company))
        latest = frame.iloc[-1]
        invested = holding.quantity * holding.average_price
        current = holding.quantity * latest["close"]
        invested_total += invested
        current_total += current
        weighted_risk += float(latest["volatility"]) * current
        rows.append(
            {
                "id": holding.id,
                "symbol": company.display_symbol,
                "quantity": holding.quantity,
                "average_price": holding.average_price,
                "current_price": round(float(latest["close"]), 2),
                "pnl": round(float(current - invested), 2),
                "pnl_percent": round(float((current - invested) / invested), 4) if invested else 0,
            }
        )
    risk = weighted_risk / current_total if current_total else 0
    return envelope(
        {
            "holdings": rows,
            "invested_value": round(invested_total, 2),
            "current_value": round(current_total, 2),
            "pnl": round(current_total - invested_total, 2),
            "risk_score": round(risk, 4),
        }
    )


@router.post("/portfolio/holdings")
def add_holding(symbol: str, quantity: float, average_price: float, db: Session = Depends(get_db)) -> dict:
    company = get_company_or_404(db, symbol)
    holding = PortfolioHolding(company_id=company.id, quantity=quantity, average_price=average_price)
    db.add(holding)
    db.commit()
    return envelope({"id": holding.id, "symbol": company.display_symbol})


@router.delete("/portfolio/holdings/{holding_id}")
def delete_holding(holding_id: int, db: Session = Depends(get_db)) -> dict:
    holding = db.get(PortfolioHolding, holding_id)
    if not holding:
        raise HTTPException(status_code=404, detail="Portfolio holding not found")
    db.delete(holding)
    db.commit()
    return envelope({"deleted": holding_id})


@router.get("/export/{symbol}.csv")
def export_csv(symbol: str, db: Session = Depends(get_db)) -> StreamingResponse:
    company = get_company_or_404(db, symbol)
    frame = calculate_indicators(ensure_prices(db, company))
    stream = StringIO()
    frame.to_csv(stream, index=False)
    stream.seek(0)
    return StreamingResponse(
        iter([stream.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename={company.display_symbol}_stocksense.csv"},
    )


@router.get("/export/{symbol}.pdf")
def export_pdf(symbol: str, db: Session = Depends(get_db)) -> StreamingResponse:
    company = get_company_or_404(db, symbol)
    frame = calculate_indicators(ensure_prices(db, company))
    rec = build_recommendation(company.display_symbol, frame)
    pred = predict_next_close(frame)
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.pdfgen import canvas
    except Exception as exc:
        raise HTTPException(status_code=500, detail="PDF export requires reportlab") from exc

    buffer = BytesIO()
    pdf = canvas.Canvas(buffer, pagesize=letter)
    pdf.setTitle(f"{company.display_symbol} StockSense Report")
    pdf.setFont("Helvetica-Bold", 18)
    pdf.drawString(72, 740, f"StockSense AI Pro Report: {company.display_symbol}")
    pdf.setFont("Helvetica", 11)
    lines = [
        f"Company: {company.name}",
        f"Latest close: {frame.iloc[-1]['close']:.2f}",
        f"Recommendation: {rec['action']} ({rec['confidence']}% confidence)",
        f"Prediction: {pred['predicted_close']} for {pred.get('predicted_for')}",
        f"Insight: {rec['insight']}",
        "Disclaimer: Educational analytics only, not financial advice.",
    ]
    y = 700
    for line in lines:
        pdf.drawString(72, y, line[:110])
        y -= 24
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return StreamingResponse(
        buffer,
        media_type="application/pdf",
        headers={"Content-Disposition": f"attachment; filename={company.display_symbol}_stocksense_report.pdf"},
    )
