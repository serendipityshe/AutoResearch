import { cn, statusLabel } from "@/lib/utils";
import type { Status } from "@/lib/types";

const styles: Record<Status, string> = {
  pending: "border-slate-300 bg-slate-100 text-slate-600",
  in_progress: "border-research/30 bg-research/10 text-research",
  blocked: "border-warn/30 bg-warn/10 text-warn",
  failed: "border-danger/30 bg-danger/10 text-danger",
  completed: "border-data/30 bg-data/10 text-data",
  skipped: "border-slate-300 bg-white/60 text-slate-500",
  aborted: "border-danger/30 bg-danger/10 text-danger",
  unknown: "border-slate-300 bg-white/60 text-slate-500",
};

export function StatusPill({ status, className }: { status: Status; className?: string }) {
  return (
    <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-semibold capitalize", styles[status], className)}>
      {statusLabel(status)}
    </span>
  );
}
