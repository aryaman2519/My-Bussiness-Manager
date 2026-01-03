const tasks = [
  {
    title: "Order Samsung S24 covers",
    status: "critical",
    due: "Today",
  },
  {
    title: "Send Redmi Note 13 invoice via WhatsApp",
    status: "pending",
    due: "Due in 2h",
  },
  {
    title: "Follow up: Warranty claim IMEI 356789102233445",
    status: "pending",
    due: "Due tomorrow",
  },
];

const badgeColor = (status: string) => {
  switch (status) {
    case "critical":
      return "bg-rose-500/20 text-rose-200";
    case "pending":
    default:
      return "bg-sky-500/20 text-sky-200";
  }
};

export const TasksCard = () => {
  return (
    <div className="card">
      <p className="text-xs uppercase tracking-[0.3em] text-slate-400">
        Today
      </p>
      <h2 className="text-2xl font-semibold">Command Queue</h2>
      <ul className="mt-4 space-y-3">
        {tasks.map((task) => (
          <li
            key={task.title}
            className="flex items-center justify-between rounded-2xl border border-slate-800 bg-slate-900/50 px-4 py-3"
          >
            <div>
              <p className="font-medium">{task.title}</p>
              <p className="text-xs text-slate-500">{task.due}</p>
            </div>
            <span className={`text-xs px-3 py-1 rounded-full ${badgeColor(task.status)}`}>
              {task.status === "critical" ? "Urgent" : "Pending"}
            </span>
          </li>
        ))}
      </ul>
    </div>
  );
};







