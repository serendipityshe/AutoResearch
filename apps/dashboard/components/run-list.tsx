import Link from "next/link";
import { ArrowUpRight, GitCommitHorizontal } from "lucide-react";
import type { RunSummary } from "@/lib/types";
import { compactId, formatDate } from "@/lib/utils";
import { StatusPill } from "@/components/status-pill";

export function RunList({ runs }: { runs: RunSummary[] }) {
  return (
    <section id="runs" className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-5 flex items-end justify-between gap-4">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-muted">实验历史</p>
          <h2 className="font-display text-3xl font-black">本地实验尝试记录</h2>
        </div>
        <span className="rounded-full border border-line bg-white/70 px-3 py-1 text-sm font-bold">{runs.length} 次实验</span>
      </div>
      {runs.length === 0 ? (
        <div className="rounded-3xl border border-dashed border-line bg-white/50 p-6 text-muted">
          暂无 `.autolab/runs` 记录。请先运行 `python plugins/matrix-autolab/scripts/autolab_run.py init-project` 并创建一次实验记录。
        </div>
      ) : (
        <div className="grid gap-3">
          {runs.map((run) => (
            <Link key={run.runId} href={`/runs/${run.runId}`} className="group rounded-3xl border border-line bg-white/72 p-4 transition hover:-translate-y-0.5 hover:shadow-panel">
              <div className="flex flex-col gap-4 md:flex-row md:items-center md:justify-between">
                <div>
                  <div className="flex flex-wrap items-center gap-2">
                    <StatusPill status={run.status} />
                    <span className="text-xs font-bold uppercase tracking-[0.18em] text-muted">{run.kind || "未知类型"}</span>
                  </div>
                  <h3 className="mt-2 text-xl font-black">{run.runId}</h3>
                  <p className="mt-1 text-sm text-muted">{run.summary || `开始时间 ${formatDate(run.startedAt)}，入口技能 ${run.entrySkill || "未知技能"}。`}</p>
                </div>
                <div className="flex flex-wrap items-center gap-3 text-sm text-muted">
                  <span className="inline-flex items-center gap-1"><GitCommitHorizontal className="h-4 w-4" /> {compactId(run.gitCommit, 8)}</span>
                  <span>{run.counts.metrics} 个指标</span>
                  <span>{run.counts.errors} 个错误</span>
                  <ArrowUpRight className="h-5 w-5 text-research transition group-hover:translate-x-1" />
                </div>
              </div>
            </Link>
          ))}
        </div>
      )}
    </section>
  );
}
