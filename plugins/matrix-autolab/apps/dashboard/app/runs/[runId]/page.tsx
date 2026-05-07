import Link from "next/link";
import { notFound } from "next/navigation";
import { ArrowLeft, Boxes, FileText, GitBranch, ListChecks } from "lucide-react";
import { DashboardShell } from "@/components/shell";
import { MetricPanel } from "@/components/metric-panel";
import { FailureLedger, ReportLibrary } from "@/components/evidence-panels";
import { StatusPill } from "@/components/status-pill";
import { getRunDetail } from "@/lib/autolab-reader";
import { compactId, formatDate } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function RunPage({ params }: { params: Promise<{ runId: string }> }) {
  const { runId } = await params;
  const warnings: string[] = [];
  const run = await getRunDetail(runId, warnings);
  if (!run) notFound();
  return (
    <DashboardShell>
      <Link href="/" className="inline-flex w-fit items-center gap-2 rounded-full border border-line bg-panel px-4 py-2 text-sm font-bold">
        <ArrowLeft className="h-4 w-4" /> 返回总览
      </Link>
      <section className="rounded-[2rem] border border-line bg-panel/90 p-6 shadow-panel">
        <div className="flex flex-col gap-5 lg:flex-row lg:items-start lg:justify-between">
          <div>
            <StatusPill status={run.status} />
            <h1 className="mt-4 font-display text-4xl font-black tracking-tight md:text-6xl">{run.runId}</h1>
            <p className="mt-3 max-w-3xl text-muted">{run.summary || `这是一次由 ${run.entrySkill || "未知技能"} 启动的 ${run.kind || "未知类型"} 实验。`}</p>
          </div>
          <div className="grid gap-2 rounded-3xl border border-line bg-white/70 p-4 text-sm text-muted">
            <span>开始时间：{formatDate(run.startedAt)}</span>
            <span>结束时间：{formatDate(run.endedAt)}</span>
            <span>论文来源：{run.paperSource || "未记录"}</span>
            <span>Git：{run.gitBranch || "未知分支"} / {compactId(run.gitCommit, 8)}</span>
          </div>
        </div>
      </section>
      <section className="grid gap-4 md:grid-cols-4">
        <MiniStat icon={<ListChecks />} label="事件" value={run.events.length} />
        <MiniStat icon={<FileText />} label="报告" value={run.reports.length} />
        <MiniStat icon={<Boxes />} label="产物" value={run.artifacts.length} />
        <MiniStat icon={<GitBranch />} label="变更文件" value={run.changedFiles.length} />
      </section>
      <MetricPanel metrics={run.metrics} />
      <div className="grid gap-6 xl:grid-cols-2">
        <FailureLedger errors={run.errors} />
        <ReportLibrary reports={run.reports} />
      </div>
      <section className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
        <p className="text-xs font-bold uppercase tracking-[0.22em] text-muted">事件时间线</p>
        <h2 className="font-display text-3xl font-black">已记录操作</h2>
        <div className="mt-5 grid gap-3">
          {run.events.length === 0 ? <p className="rounded-3xl border border-dashed border-line bg-white/50 p-5 text-muted">暂无事件记录。</p> : null}
          {run.events.slice(0, 24).map((event, index) => (
            <article key={`${event.timestamp}-${index}`} className="rounded-3xl border border-line bg-white/72 p-4">
              <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted">{formatDate(event.timestamp)} / {event.eventType}</p>
              <h3 className="mt-1 font-black">{event.message || "暂无消息"}</h3>
              <p className="mt-2 text-sm text-muted">{event.skill || "未知技能"} {event.phase ? `位于 ${event.phase}` : ""}</p>
            </article>
          ))}
        </div>
      </section>
    </DashboardShell>
  );
}

function MiniStat({ icon, label, value }: { icon: React.ReactNode; label: string; value: number }) {
  return (
    <article className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-4 flex h-10 w-10 items-center justify-center rounded-2xl bg-ink text-white">{icon}</div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted">{label}</p>
      <h2 className="mt-2 text-3xl font-black">{value}</h2>
    </article>
  );
}
