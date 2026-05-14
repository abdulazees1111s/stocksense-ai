import { Bot, Send } from "lucide-react";
import { useMemo, useState } from "react";

const prompts = [
  "Why is this stock rated this way?",
  "What changed today?",
  "Which stock is riskiest?",
  "Explain the prediction.",
];

export function Assistant({ selected, summary, recommendation, prediction, sentiment, overview }) {
  const [answer, setAnswer] = useState("");

  const riskiest = useMemo(() => {
    if (!overview?.length) return null;
    return [...overview].sort((a, b) => b.volatility - a.volatility)[0];
  }, [overview]);

  function ask(prompt) {
    if (prompt.includes("rated")) {
      setAnswer(recommendation?.insight || `${selected} is waiting for enough data to form a recommendation.`);
    } else if (prompt.includes("changed")) {
      setAnswer(`${selected} last moved ${((summary?.daily_return || 0) * 100).toFixed(2)}% with latest close around ₹${summary?.latest_close || "--"}.`);
    } else if (prompt.includes("riskiest")) {
      setAnswer(riskiest ? `${riskiest.symbol} currently has the highest volatility in this watch universe at ${(riskiest.volatility * 100).toFixed(2)}%.` : "Risk data is loading.");
    } else {
      setAnswer(`The model expects ₹${prediction?.predicted_close || "--"} next, with ${prediction?.confidence || 0}% confidence. ${prediction?.note || ""}`);
    }
  }

  return (
    <section className="panel p-4">
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="icon-shell text-gain">
            <Bot size={18} />
          </div>
          <div>
            <h3 className="text-lg font-semibold text-white">Ask StockSense</h3>
            <p className="text-sm text-slate-500">Local analyst assistant</p>
          </div>
        </div>
        <p className="text-xs text-slate-500">Sentiment {sentiment?.compound?.toFixed?.(2) || "0.00"}</p>
      </div>
      <div className="mt-4 flex flex-wrap gap-2">
        {prompts.map((prompt) => (
          <button key={prompt} onClick={() => ask(prompt)} className="seg">
            {prompt}
          </button>
        ))}
      </div>
      <div className="mt-4 rounded-lg border border-line bg-black/20 p-4 text-sm leading-6 text-slate-300">
        {answer || "Select a prompt to generate a context-aware answer from the current analytics."}
      </div>
      <button onClick={() => ask("Why is this stock rated this way?")} className="btn mt-4">
        <Send size={16} />
        Generate insight
      </button>
    </section>
  );
}
