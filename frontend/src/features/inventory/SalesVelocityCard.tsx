const velocityInsights = [
  {
    name: "Redmi Note 13 Pro",
    dailyVelocity: 3.2,
    onHand: 5,
    leadTimeDays: 2,
    recommendation: "Reorder 15 units",
    landingCost: 18500,
  },
  {
    name: "OnePlus Buds 3",
    dailyVelocity: 1.4,
    onHand: 12,
    leadTimeDays: 5,
    recommendation: "Monitor - reorder next week",
    landingCost: 3200,
  },
];

interface SalesVelocityCardProps {
  showCosts?: boolean;
}

export const SalesVelocityCard = ({ showCosts = false }: SalesVelocityCardProps) => {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
        Forecast
      </p>
      <h2 className="text-2xl font-semibold text-white">Dynamic Restock Predictions</h2>
      <p className="text-sm text-slate-400 mb-4">
        ML-powered forecasting with seasonality detection
      </p>
      <div className="space-y-4">
        {velocityInsights.map((item) => (
          <div
            key={item.name}
            className="rounded-2xl border border-slate-800 bg-slate-900/50 p-4"
          >
            <h3 className="font-semibold text-white">{item.name}</h3>
            <p className="text-xs text-slate-500 mt-1">
              {item.dailyVelocity} units/day • On hand {item.onHand} • Lead time{" "}
              {item.leadTimeDays}d
              {showCosts && ` • Landing Cost: ₹${item.landingCost.toLocaleString("en-IN")}`}
            </p>
            <p className="mt-2 text-sm text-emerald-300">
              {item.recommendation}
            </p>
          </div>
        ))}
      </div>
    </div>
  );
};







