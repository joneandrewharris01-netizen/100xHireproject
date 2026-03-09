"use client";

type Status = "pending" | "running" | "done" | "error";

const STATUS_CONFIG: Record<Status, { color: string; bg: string; label: string }> = {
  pending: { color: "text-gray-400", bg: "bg-gray-400/10", label: "Pending" },
  running: { color: "text-yellow-400", bg: "bg-yellow-400/10", label: "Running" },
  done: { color: "text-green-400", bg: "bg-green-400/10", label: "Done" },
  error: { color: "text-red-400", bg: "bg-red-400/10", label: "Error" },
};

export function StatusBadge({ status }: { status: Status }) {
  const cfg = STATUS_CONFIG[status];
  return (
    <span className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-full text-xs font-medium ${cfg.color} ${cfg.bg}`}>
      <span className={`w-1.5 h-1.5 rounded-full ${status === "running" ? "animate-pulse" : ""} ${cfg.color.replace("text-", "bg-")}`} />
      {cfg.label}
    </span>
  );
}
