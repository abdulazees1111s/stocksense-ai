import {
  BarElement,
  CategoryScale,
  Chart as ChartJS,
  LinearScale,
  Tooltip,
} from "chart.js";
import { Bar } from "react-chartjs-2";

ChartJS.register(CategoryScale, LinearScale, BarElement, Tooltip);

export function VolumeChart({ rows }) {
  if (!rows?.length) {
    return <div className="chart-empty">No volume data</div>;
  }
  return (
    <div className="h-[360px]">
      <Bar
        data={{
          labels: rows.map((row) => row.date),
          datasets: [
            {
              label: "Volume",
              data: rows.map((row) => row.volume),
              backgroundColor: rows.map((row) => (row.close >= row.open ? "rgba(45,212,191,0.48)" : "rgba(251,113,133,0.48)")),
              borderRadius: 3,
            },
          ],
        }}
        options={{
          responsive: true,
          maintainAspectRatio: false,
          plugins: { legend: { display: false } },
          scales: {
            x: { ticks: { display: false }, grid: { display: false } },
            y: { ticks: { color: "#64748b", maxTicksLimit: 5 }, grid: { color: "rgba(148,163,184,0.08)" } },
          },
        }}
      />
    </div>
  );
}
