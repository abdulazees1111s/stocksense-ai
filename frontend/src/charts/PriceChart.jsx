import {
  CategoryScale,
  Chart as ChartJS,
  Legend,
  LinearScale,
  LineElement,
  PointElement,
  Tooltip,
} from "chart.js";
import { Line } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, PointElement, LineElement, Tooltip, Legend);

export function PriceChart({ rows, prediction }) {
  if (!rows?.length) {
    return <div className="chart-empty">No prediction data</div>;
  }
  const labels = rows.map((row) => row.date);
  const close = rows.map((row) => row.close);
  const predictionSeries = [...new Array(Math.max(0, close.length - 1)).fill(null), close[close.length - 1], prediction?.predicted_close || null];
  const predictionLabels = [...labels, prediction?.predicted_for || "Next"];
  return (
    <Line
      data={{
        labels: predictionLabels,
        datasets: [
          {
            label: "Close",
            data: close,
            borderColor: "#2dd4bf",
            backgroundColor: "rgba(45,212,191,0.16)",
            tension: 0.35,
            pointRadius: 0,
          },
          {
            label: "Prediction",
            data: predictionSeries,
            borderColor: "#fbbf24",
            borderDash: [6, 6],
            tension: 0.25,
            pointRadius: 3,
          },
        ],
      }}
      options={{
        responsive: true,
        maintainAspectRatio: false,
        plugins: { legend: { labels: { color: "#94a3b8" } } },
        scales: {
          x: { ticks: { color: "#64748b", maxTicksLimit: 7 }, grid: { color: "rgba(148,163,184,0.08)" } },
          y: { ticks: { color: "#64748b" }, grid: { color: "rgba(148,163,184,0.08)" } },
        },
      }}
    />
  );
}
