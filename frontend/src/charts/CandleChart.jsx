import Plot from "react-plotly.js";

const layout = {
  paper_bgcolor: "rgba(0,0,0,0)",
  plot_bgcolor: "rgba(0,0,0,0)",
  margin: { t: 12, r: 18, b: 36, l: 42 },
  height: 360,
  font: { color: "#94a3b8" },
  xaxis: { gridcolor: "rgba(148,163,184,0.08)", rangeslider: { visible: false } },
  yaxis: { gridcolor: "rgba(148,163,184,0.08)" },
};

export function CandleChart({ rows }) {
  if (!rows?.length) {
    return <div className="chart-empty">No price data</div>;
  }
  return (
    <Plot
      className="w-full"
      data={[
        {
          x: rows.map((row) => row.date),
          open: rows.map((row) => row.open),
          high: rows.map((row) => row.high),
          low: rows.map((row) => row.low),
          close: rows.map((row) => row.close),
          type: "candlestick",
          increasing: { line: { color: "#2dd4bf" } },
          decreasing: { line: { color: "#fb7185" } },
        },
      ]}
      layout={layout}
      config={{ displayModeBar: true, responsive: true }}
      useResizeHandler
      style={{ width: "100%", height: "360px" }}
    />
  );
}
