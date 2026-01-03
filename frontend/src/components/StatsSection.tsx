export const StatsSection = () => {
  const stats = [
    { value: "99.9%", label: "Uptime", icon: "⚡" },
    { value: "50+", label: "Products Tracked", icon: "📦" },
    { value: "₹2.5L+", label: "Revenue Optimized", icon: "💰" },
    { value: "24/7", label: "Alerts Active", icon: "🔔" }
  ];

  return (
    <section className="py-12 px-6 bg-slate-900/30 border-y border-slate-800/50">
      <div className="max-w-6xl mx-auto">
        <div className="grid grid-cols-2 md:grid-cols-4 gap-8">
          {stats.map((stat, idx) => (
            <div key={idx} className="text-center">
              <div className="text-3xl mb-2">{stat.icon}</div>
              <div className="text-2xl md:text-3xl font-bold text-white mb-1">
                {stat.value}
              </div>
              <div className="text-slate-400 text-xs font-medium">{stat.label}</div>
            </div>
          ))}
        </div>
      </div>
    </section>
  );
};

