export function Heatmap({ items }) {
  if (!items?.length) {
    return <div className="chart-empty">No heatmap data</div>;
  }
  return (
    <div className="grid grid-cols-2 gap-3 sm:grid-cols-3">
      {items.map((item) => {
        const gain = item.change >= 0;
        const intensity = Math.min(0.45, 0.12 + Math.abs(item.change) * 5);
        return (
          <button
            key={item.symbol}
            className="min-h-[112px] rounded-lg border border-line p-4 text-left transition hover:scale-[1.02]"
            style={{ backgroundColor: gain ? `rgba(45,212,191,${intensity})` : `rgba(251,113,133,${intensity})` }}
          >
            <p className="text-lg font-semibold text-white">{item.symbol}</p>
            <p className="mt-1 text-xs text-slate-300">{item.sector}</p>
            <p className={gain ? "mt-4 text-2xl font-semibold text-teal-100" : "mt-4 text-2xl font-semibold text-rose-100"}>
              {(item.change * 100).toFixed(2)}%
            </p>
          </button>
        );
      })}
    </div>
  );
}
