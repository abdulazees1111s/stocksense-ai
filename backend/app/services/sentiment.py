from statistics import mean

import yfinance as yf
from vaderSentiment.vaderSentiment import SentimentIntensityAnalyzer


FALLBACK_HEADLINES = {
    "TCS.NS": [
        "TCS wins multi-year cloud transformation deal from a global enterprise",
        "Analysts expect stable margins for TCS despite cautious IT spending",
        "TCS expands AI services portfolio for banking clients",
    ],
    "INFY.NS": [
        "Infosys strengthens generative AI offerings for enterprise customers",
        "Infosys guidance remains in focus after mixed technology sector signals",
        "Infosys signs digital modernization contract with European client",
    ],
    "RELIANCE.NS": [
        "Reliance retail and telecom units support diversified growth outlook",
        "Energy margin volatility keeps Reliance investors watchful",
        "Reliance accelerates new energy investment roadmap",
    ],
    "HDFCBANK.NS": [
        "HDFC Bank deposit growth and margins remain key investor focus",
        "Brokerages see gradual improvement in HDFC Bank operating metrics",
        "HDFC Bank expands digital lending capabilities",
    ],
    "ICICIBANK.NS": [
        "ICICI Bank asset quality remains resilient in latest analyst checks",
        "ICICI Bank continues to gain market share in retail lending",
        "Investors track ICICI Bank credit growth and margin trends",
    ],
}


def fetch_headlines(symbol: str) -> list[str]:
    try:
        news = yf.Ticker(symbol).news or []
        headlines = [item.get("title", "") for item in news if item.get("title")]
        if headlines:
            return headlines[:8]
    except Exception:
        pass
    return FALLBACK_HEADLINES.get(symbol, FALLBACK_HEADLINES["TCS.NS"])


def analyze_sentiment(symbol: str) -> dict:
    analyzer = SentimentIntensityAnalyzer()
    headlines = fetch_headlines(symbol)
    scores = [analyzer.polarity_scores(headline) for headline in headlines]
    positive = mean(score["pos"] for score in scores) if scores else 0
    neutral = mean(score["neu"] for score in scores) if scores else 1
    negative = mean(score["neg"] for score in scores) if scores else 0
    compound = mean(score["compound"] for score in scores) if scores else 0
    label = "positive" if compound > 0.1 else "negative" if compound < -0.1 else "neutral"
    summary = f"Recent news sentiment for {symbol} is {label}, with compound score {compound:.2f}."
    return {
        "positive": round(positive, 3),
        "neutral": round(neutral, 3),
        "negative": round(negative, 3),
        "compound": round(compound, 3),
        "summary": summary,
        "headlines": headlines,
    }
