import { useCallback, useEffect, useMemo, useState } from "react";
import { createRoot } from "react-dom/client";
import {
  Activity,
  BarChart3,
  Bot,
  CandlestickChart,
  CircleDollarSign,
  Download,
  Flame,
  Gauge,
  Heart,
  LineChart,
  Loader2,
  RefreshCw,
  Search,
  ShieldAlert,
  Sparkles,
  Star,
  TrendingUp,
  WalletCards,
} from "lucide-react";
import "./styles.css";
import { api } from "./lib/api";
import { CandleChart } from "./charts/CandleChart";
import { PriceChart } from "./charts/PriceChart";
import { VolumeChart } from "./charts/VolumeChart";
import { Heatmap } from "./components/Heatmap";
import { Assistant } from "./components/Assistant";

const ranges = ["7D", "30D", "90D", "1Y"];
const fallbackCompanies = [
  { symbol: "TCS", name: "Tata Consultancy Services" },
  { symbol: "INFY", name: "Infosys" },
  { symbol: "RELIANCE", name: "Reliance Industries" },
  { symbol: "HDFCBANK", name: "HDFC Bank" },
  { symbol: "ICICIBANK", name: "ICICI Bank" },
];

function classNames(...items) {
  return items.filter(Boolean).join(" ");
}

function MetricCard({ icon: Icon, label, value, tone = "neutral", sub }) {
  return (
    <section className="panel min-h-[118px] p-4">
      <div className="flex items-start justify-between gap-3">
        <div>
          <p className="text-xs uppercase tracking-[0.18em] text-slate-500">{label}</p>
          <p className="mt-3 text-2xl font-semibold text-white">{value}</p>
          {sub ? <p className="mt-1 text-sm text-slate-400">{sub}</p> : null}
        </div>
        <div className={classNames("icon-shell", tone === "gain" && "text-gain", tone === "loss" && "text-loss")}>
          <Icon size={19} />
        </div>
      </div>
    </section>
  );
}

function Badge({ value }) {
  const tone = value === "BUY" ? "bg-teal-400/14 text-teal-200" : value === "SELL" ? "bg-rose-400/14 text-rose-200" : "bg-amber-400/14 text-amber-200";
  return <span className={classNames("rounded px-2 py-1 text-xs font-semibold", tone)}>{value}</span>;
}

function App() {
  const [companies, setCompanies] = useState(fallbackCompanies);
  const [selected, setSelected] = useState("TCS");
  const [compareWith, setCompareWith] = useState("INFY");
  const [range, setRange] = useState("30D");
  const [overview, setOverview] = useState([]);
  const [heatmap, setHeatmap] = useState([]);
  const [prices, setPrices] = useState([]);
  const [summary, setSummary] = useState(null);
  const [recommendation, setRecommendation] = useState(null);
  const [prediction, setPrediction] = useState(null);
  const [sentiment, setSentiment] = useState(null);
  const [comparison, setComparison] = useState(null);
  const [portfolio, setPortfolio] = useState(null);
  const [watchlist, setWatchlist] = useState(["TCS", "INFY"]);
  const [loading, setLoading] = useState(true);
  const [refreshing, setRefreshing] = useState(false);
  const [error, setError] = useState("");
  const [lastUpdated, setLastUpdated] = useState(null);

  const loadAll = useCallback(async (isRefresh = false) => {
    try {
      setError("");
      isRefresh ? setRefreshing(true) : setLoading(true);
      const [companyRes, overviewRes, heatmapRes, dataRes, summaryRes, recRes, predRes, sentRes, compareRes, portfolioRes, watchlistRes] =
        await Promise.all([
          api.companies(),
          api.overview(),
          api.heatmap(),
          api.stockData(selected, range),
          api.summary(selected),
          api.recommendation(selected),
          api.prediction(selected),
          api.sentiment(selected),
          api.compare(selected, compareWith),
          api.portfolio(),
          api.watchlist(),
        ]);
      setCompanies(companyRes.data.length ? companyRes.data : fallbackCompanies);
      setOverview(overviewRes.data);
      setHeatmap(heatmapRes.data);
      setPrices(dataRes.data);
      setSummary(summaryRes.data);
      setRecommendation(recRes.data);
      setPrediction(predRes.data);
      setSentiment(sentRes.data);
      setComparison(compareRes.data);
      setPortfolio(portfolioRes.data);
      if (watchlistRes.data.length) {
        setWatchlist(watchlistRes.data.map((item) => item.symbol));
      }
      setLastUpdated(new Date());
    } catch (err) {
      setError(err.message);
    } finally {
      setLoading(false);
      setRefreshing(false);
    }
  }, [compareWith, range, selected]);

  useEffect(() => {
    loadAll(false);
    const timer = setInterval(() => loadAll(true), 30000);
    return () => clearInterval(timer);
  }, [loadAll]);

  const sortedOverview = useMemo(() => [...overview].sort((a, b) => b.change - a.change), [overview]);
  const riskPercent = Math.min(100, Math.round((summary?.volatility || 0) * 180));

  async function toggleWatch(symbol) {
    const exists = watchlist.includes(symbol);
    exists ? await api.deleteWatchlist(symbol) : await api.addWatchlist(symbol);
    setWatchlist((items) => (exists ? items.filter((item) => item !== symbol) : [...items, symbol]));
  }

  return (
    <main className="min-h-screen bg-ink text-slate-200">
      <div className="grid min-h-screen lg:grid-cols-[260px_1fr]">
        <aside className="hidden border-r border-line bg-black/20 p-5 lg:block">
          <div className="flex items-center gap-3">
            <div className="grid h-11 w-11 place-items-center rounded-lg bg-teal-400/15 text-gain">
              <Sparkles size={22} />
            </div>
            <div>
              <h1 className="text-lg font-semibold text-white">StockSense AI Pro</h1>
              <p className="text-xs text-slate-500">NSE Intelligence Desk</p>
            </div>
          </div>
          <nav className="mt-8 space-y-2 text-sm">
            {[
              ["Overview", BarChart3],
              ["AI Insights", Bot],
              ["Risk", Gauge],
              ["Compare", LineChart],
              ["Portfolio", WalletCards],
            ].map(([label, Icon]) => (
              <a key={label} className="flex items-center gap-3 rounded-lg px-3 py-2 text-slate-400 transition hover:bg-white/5 hover:text-white">
                <Icon size={17} />
                {label}
              </a>
            ))}
          </nav>
          <section className="mt-8 rounded-lg border border-line bg-white/[0.03] p-4">
            <p className="text-xs uppercase tracking-[0.18em] text-slate-500">Watchlist</p>
            <div className="mt-4 space-y-2">
              {watchlist.map((symbol) => (
                <button key={symbol} onClick={() => setSelected(symbol)} className="flex w-full items-center justify-between rounded-md px-2 py-2 text-sm hover:bg-white/5">
                  <span>{symbol}</span>
                  <Star size={15} className="text-amber" />
                </button>
              ))}
            </div>
          </section>
        </aside>

        <section className="p-4 sm:p-6 xl:p-8">
          <header className="flex flex-col gap-4 border-b border-line pb-5 xl:flex-row xl:items-center xl:justify-between">
            <div>
              <p className="text-sm text-slate-500">Live dashboard</p>
              <h2 className="text-2xl font-semibold text-white sm:text-3xl">AI Market Intelligence</h2>
            </div>
            <div className="flex flex-wrap items-center gap-3">
              <div className="flex items-center gap-2 rounded-lg border border-line bg-white/[0.03] px-3 py-2">
                <Search size={16} className="text-slate-500" />
                <select value={selected} onChange={(event) => setSelected(event.target.value)} className="bg-transparent text-sm text-white outline-none">
                  {companies.map((company) => (
                    <option key={company.symbol} value={company.symbol} className="bg-slate-950">
                      {company.symbol}
                    </option>
                  ))}
                </select>
              </div>
              <button onClick={() => loadAll(true)} className="btn">
                <RefreshCw size={16} className={refreshing ? "animate-spin" : ""} />
                Refresh
              </button>
            </div>
          </header>

          {error ? (
            <div className="mt-5 rounded-lg border border-rose-400/30 bg-rose-500/10 px-4 py-3 text-sm text-rose-100">
              {error}. Start the backend and run ingestion if this is the first launch.
            </div>
          ) : null}

          {loading ? (
            <div className="grid min-h-[60vh] place-items-center">
              <Loader2 className="animate-spin text-gain" size={36} />
            </div>
          ) : (
            <div className="mt-6 space-y-6">
              <div className="grid gap-4 md:grid-cols-2 xl:grid-cols-4">
                <MetricCard icon={CircleDollarSign} label="Latest close" value={`₹${summary?.latest_close ?? "--"}`} sub={selected} tone="gain" />
                <MetricCard icon={TrendingUp} label="30D volatility" value={`${Math.round((summary?.volatility || 0) * 100)}%`} sub="Annualized risk" />
                <MetricCard icon={Flame} label="AI action" value={<Badge value={recommendation?.action || "HOLD"} />} sub={`${recommendation?.confidence || 0}% confidence`} />
                <MetricCard icon={Activity} label="Sentiment" value={(sentiment?.compound || 0).toFixed(2)} sub={sentiment?.summary || "Neutral"} />
              </div>

              <div className="grid gap-6 xl:grid-cols-[1.5fr_0.85fr]">
                <section className="panel p-4">
                  <div className="flex flex-col gap-3 sm:flex-row sm:items-center sm:justify-between">
                    <div>
                      <h3 className="text-lg font-semibold text-white">{selected} Price Action</h3>
                      <p className="text-sm text-slate-500">{lastUpdated ? `Updated ${lastUpdated.toLocaleTimeString()}` : "Awaiting data"}</p>
                    </div>
                    <div className="flex gap-2">
                      {ranges.map((item) => (
                        <button key={item} onClick={() => setRange(item)} className={classNames("seg", range === item && "seg-active")}>
                          {item}
                        </button>
                      ))}
                    </div>
                  </div>
                  <div className="mt-4 grid gap-4 xl:grid-cols-[1fr_220px]">
                    <CandleChart rows={prices} />
                    <VolumeChart rows={prices} />
                  </div>
                </section>

                <section className="panel p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">AI Insight</h3>
                    <Bot className="text-gain" size={20} />
                  </div>
                  <p className="mt-4 text-sm leading-6 text-slate-300">{recommendation?.insight}</p>
                  <div className="mt-5 grid grid-cols-2 gap-3">
                    <div className="rounded-lg border border-line p-3">
                      <p className="text-xs text-slate-500">Prediction</p>
                      <p className="mt-1 text-xl font-semibold text-white">₹{prediction?.predicted_close}</p>
                      <p className="text-xs text-slate-500">{prediction?.confidence}% model confidence</p>
                    </div>
                    <div className="rounded-lg border border-line p-3">
                      <p className="text-xs text-slate-500">Risk meter</p>
                      <div className="mt-3 h-2 rounded-full bg-slate-800">
                        <div className="h-2 rounded-full bg-gradient-to-r from-teal-400 to-amber-300" style={{ width: `${riskPercent}%` }} />
                      </div>
                      <p className="mt-2 text-xs text-slate-500">{riskPercent}/100</p>
                    </div>
                  </div>
                  <div className="mt-4 flex gap-2">
                    <a className="btn flex-1 justify-center" href={api.csvUrl(selected)}>
                      <Download size={16} />
                      CSV
                    </a>
                    <a className="btn flex-1 justify-center" href={api.pdfUrl(selected)}>
                      <Download size={16} />
                      PDF
                    </a>
                  </div>
                </section>
              </div>

              <div className="grid gap-6 xl:grid-cols-[1fr_1fr]">
                <section className="panel p-4">
                  <h3 className="text-lg font-semibold text-white">Prediction Path</h3>
                  <PriceChart rows={prices} prediction={prediction} />
                </section>
                <section className="panel p-4">
                  <h3 className="text-lg font-semibold text-white">Market Heatmap</h3>
                  <Heatmap items={heatmap} />
                </section>
              </div>

              <div className="grid gap-6 xl:grid-cols-[0.9fr_1.1fr]">
                <section className="panel p-4">
                  <div className="flex items-center justify-between">
                    <h3 className="text-lg font-semibold text-white">Trending Stocks</h3>
                    <CandlestickChart size={20} className="text-gain" />
                  </div>
                  <div className="mt-4 space-y-2">
                    {sortedOverview.map((item) => (
                      <button key={item.symbol} onClick={() => setSelected(item.symbol)} className="flex w-full items-center justify-between rounded-lg border border-line p-3 text-left hover:bg-white/[0.04]">
                        <div>
                          <p className="font-medium text-white">{item.symbol}</p>
                          <p className="text-xs text-slate-500">{item.name}</p>
                        </div>
                        <div className="flex items-center gap-3">
                          <span className={item.change >= 0 ? "text-gain" : "text-loss"}>{(item.change * 100).toFixed(2)}%</span>
                          <button onClick={(event) => { event.stopPropagation(); toggleWatch(item.symbol); }} className="icon-button">
                            <Heart size={16} className={watchlist.includes(item.symbol) ? "fill-amber text-amber" : ""} />
                          </button>
                        </div>
                      </button>
                    ))}
                  </div>
                </section>

                <section className="panel p-4">
                  <div className="flex flex-wrap items-center justify-between gap-3">
                    <h3 className="text-lg font-semibold text-white">Compare Stocks</h3>
                    <select value={compareWith} onChange={(event) => setCompareWith(event.target.value)} className="rounded-lg border border-line bg-slate-950 px-3 py-2 text-sm text-white">
                      {companies.filter((company) => company.symbol !== selected).map((company) => (
                        <option key={company.symbol} value={company.symbol}>{company.symbol}</option>
                      ))}
                    </select>
                  </div>
                  <div className="mt-4 grid gap-3 sm:grid-cols-2">
                    {comparison?.stocks?.map((stock) => (
                      <div key={stock.symbol} className="rounded-lg border border-line p-4">
                        <div className="flex items-center justify-between">
                          <p className="text-xl font-semibold text-white">{stock.symbol}</p>
                          <Badge value={stock.recommendation} />
                        </div>
                        <p className="mt-3 text-sm text-slate-400">Close ₹{stock.latest_close}</p>
                        <p className={classNames("mt-1 text-sm", stock.return_30d >= 0 ? "text-gain" : "text-loss")}>30D return {(stock.return_30d * 100).toFixed(2)}%</p>
                        <p className="mt-1 text-sm text-slate-400">Volatility {(stock.volatility * 100).toFixed(2)}%</p>
                      </div>
                    ))}
                  </div>
                  <div className="mt-4 rounded-lg border border-line p-4">
                    <div className="flex items-center gap-2 text-sm text-slate-300">
                      <ShieldAlert size={17} className="text-amber" />
                      Portfolio value ₹{portfolio?.current_value || 0} with risk score {portfolio?.risk_score || 0}
                    </div>
                  </div>
                </section>
              </div>

              <Assistant selected={selected} summary={summary} recommendation={recommendation} prediction={prediction} sentiment={sentiment} overview={overview} />
            </div>
          )}
        </section>
      </div>
    </main>
  );
}

createRoot(document.getElementById("root")).render(<App />);
