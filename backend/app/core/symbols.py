from dataclasses import dataclass


@dataclass(frozen=True)
class CompanySeed:
    symbol: str
    display_symbol: str
    name: str
    sector: str
    exchange: str = "NSE"


SUPPORTED_COMPANIES: tuple[CompanySeed, ...] = (
    CompanySeed("TCS.NS", "TCS", "Tata Consultancy Services", "Information Technology"),
    CompanySeed("INFY.NS", "INFY", "Infosys", "Information Technology"),
    CompanySeed("RELIANCE.NS", "RELIANCE", "Reliance Industries", "Energy & Conglomerate"),
    CompanySeed("HDFCBANK.NS", "HDFCBANK", "HDFC Bank", "Banking"),
    CompanySeed("ICICIBANK.NS", "ICICIBANK", "ICICI Bank", "Banking"),
)


SYMBOL_ALIASES = {
    seed.display_symbol.upper(): seed.symbol for seed in SUPPORTED_COMPANIES
} | {seed.symbol.upper(): seed.symbol for seed in SUPPORTED_COMPANIES}


def normalize_symbol(symbol: str) -> str:
    normalized = symbol.strip().upper()
    if normalized in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[normalized]
    if not normalized.endswith(".NS"):
        normalized = f"{normalized}.NS"
    if normalized in SYMBOL_ALIASES:
        return SYMBOL_ALIASES[normalized]
    return normalized


def is_supported_symbol(symbol: str) -> bool:
    return normalize_symbol(symbol) in {seed.symbol for seed in SUPPORTED_COMPANIES}
