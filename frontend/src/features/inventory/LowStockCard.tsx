const dummyLowStock = [
  {
    sku: "IPHN-15-TYPEC",
    name: "Type-C Cable (Anker 60W)",
    daysRemaining: 1.8,
    status: "critical",
  },
  {
    sku: "PIX-8-CASE-CLEAR",
    name: "Pixel 8 Clear Case",
    daysRemaining: 4.2,
    status: "warning",
  },
  {
    sku: "S24U-TEMPGLASS",
    name: "Galaxy S24 Ultra Tempered Glass",
    daysRemaining: 7.9,
    status: "ok",
  },
];

const statusColors = {
  critical: "#f87171",
  warning: "#facc15",
  ok: "#34d399",
};

interface LowStockCardProps {
  showProfitMargins?: boolean;
}

export const LowStockCard = ({ showProfitMargins = false }: LowStockCardProps) => {
  return (
    <div className="card">
      <div className="flex items-center justify-between mb-4">
        <div>
          <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
            Inventory
          </p>
          <h2 className="text-2xl font-semibold text-white">Low-Stock Watchtower</h2>
        </div>
        <span className="text-xs px-3 py-1 rounded-full bg-slate-800 border border-slate-700 text-slate-200">
          Velocity-based
        </span>
      </div>
      <div className="space-y-3">
        {dummyLowStock.map((item) => (
          <div
            key={item.sku}
            className="flex items-center justify-between rounded-xl bg-slate-900/80 px-4 py-3 border border-slate-800"
          >
            <div>
              <p className="text-sm text-slate-300">{item.name}</p>
              <p className="text-xs text-slate-500">{item.sku}</p>
            </div>
            <div className="text-right">
              <p className="text-xl font-bold text-white">
                {item.daysRemaining.toFixed(1)}d
              </p>
              <p
                className="text-xs font-medium"
                style={{ color: statusColors[item.status as keyof typeof statusColors] }}
              >
                {item.status === "critical" && "Urgent"}
                {item.status === "warning" && "Plan Reorder"}
                {item.status === "ok" && "Monitored"}
              </p>
            </div>
          </div>
        ))}
      </div>
    </div>
  );
};







