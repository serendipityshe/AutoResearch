import { Database, FileStack, Route, TestTube2 } from "lucide-react";
import { DashboardShell } from "@/components/shell";
import { WorkflowMap } from "@/components/workflow-map";
import { RunList } from "@/components/run-list";
import { MetricPanel } from "@/components/metric-panel";
import { FailureLedger, ReportLibrary, SyncReadiness } from "@/components/evidence-panels";
import { getDashboardData } from "@/lib/autolab-reader";
import { compactId, statusLabel } from "@/lib/utils";

export const dynamic = "force-dynamic";

export default async function Page() {
  const data = await getDashboardData();
  const reports = [...(data.activeRun?.reports ?? []), ...data.legacyReports];
  return (
    <DashboardShell>
      <section className="grid gap-4 md:grid-cols-4">
        <StatCard icon={<Database />} label="项目" value={data.project.name} detail={data.project.initialized ? data.project.projectId : "尚未初始化"} />
        <StatCard icon={<Route />} label="当前实验" value={compactId(data.project.activeRunId, 18)} detail={data.activeRun ? statusLabel(data.activeRun.status) : "暂无当前实验"} />
        <StatCard icon={<TestTube2 />} label="指标" value={String(data.activeRun?.metrics.length ?? 0)} detail="已记录指标点" />
        <StatCard icon={<FileStack />} label="报告" value={String(reports.length)} detail="已索引实验依据" />
      </section>

      {data.project.warnings.length > 0 ? (
        <section className="rounded-[2rem] border border-warn/30 bg-warn/10 p-5 text-sm text-ink">
          <p className="mb-2 font-black">面板提示</p>
          <ul className="grid gap-1 text-muted">
            {data.project.warnings.map((warning, index) => <li key={`${warning}-${index}`}>{warning}</li>)}
          </ul>
        </section>
      ) : null}

      <WorkflowMap skills={data.skills} />
      <div className="grid gap-6 xl:grid-cols-[1.2fr_.8fr]">
        <RunList runs={data.runs} />
        <MetricPanel metrics={data.activeRun?.metrics ?? []} />
      </div>
      <div className="grid gap-6 xl:grid-cols-2">
        <FailureLedger errors={data.activeRun?.errors ?? []} />
        <ReportLibrary reports={reports} />
      </div>
      <SyncReadiness />
    </DashboardShell>
  );
}

function StatCard({ icon, label, value, detail }: { icon: React.ReactNode; label: string; value: string; detail: string }) {
  return (
    <article className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-4 flex h-11 w-11 items-center justify-center rounded-2xl bg-ink text-white">{icon}</div>
      <p className="text-xs font-bold uppercase tracking-[0.2em] text-muted">{label}</p>
      <h2 className="mt-2 truncate text-2xl font-black">{value || "暂无"}</h2>
      <p className="mt-1 truncate text-sm text-muted">{detail}</p>
    </article>
  );
}
