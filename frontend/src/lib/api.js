const API_BASE = import.meta.env.VITE_API_BASE_URL || "http://localhost:8000";

async function request(path, options = {}) {
  const response = await fetch(`${API_BASE}${path}`, options);
  const payload = await response.json().catch(() => ({}));
  if (!response.ok) {
    throw new Error(payload.detail || "StockSense API request failed");
  }
  return payload;
}

export const api = {
  baseUrl: API_BASE,
  health: () => request("/health"),
  companies: () => request("/companies"),
  overview: () => request("/market/overview"),
  heatmap: () => request("/market/heatmap"),
  stockData: (symbol, range) => request(`/data/${symbol}?range=${range}`),
  summary: (symbol) => request(`/summary/${symbol}`),
  indicators: (symbol) => request(`/indicators/${symbol}`),
  recommendation: (symbol) => request(`/recommendation/${symbol}`),
  prediction: (symbol) => request(`/predict/${symbol}`),
  sentiment: (symbol) => request(`/sentiment/${symbol}`),
  compare: (symbol1, symbol2) => request(`/compare?symbol1=${symbol1}&symbol2=${symbol2}`),
  watchlist: () => request("/watchlist"),
  addWatchlist: (symbol) => request(`/watchlist/${symbol}`, { method: "POST" }),
  deleteWatchlist: (symbol) => request(`/watchlist/${symbol}`, { method: "DELETE" }),
  portfolio: () => request("/portfolio"),
  csvUrl: (symbol) => `${API_BASE}/export/${symbol}.csv`,
  pdfUrl: (symbol) => `${API_BASE}/export/${symbol}.pdf`,
};
