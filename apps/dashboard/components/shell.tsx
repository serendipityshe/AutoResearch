import Link from "next/link";
import { Activity, DatabaseZap, FlaskConical, Gauge, GitBranch, ShieldCheck } from "lucide-react";

export function DashboardShell({ children }: { children: React.ReactNode }) {
  return (
    <main className="grid-paper min-h-screen px-5 py-6 text-ink md:px-8">
      <div className="mx-auto flex max-w-7xl flex-col gap-6">
        <header className="overflow-hidden rounded-[2rem] border border-line bg-panel/88 p-6 shadow-panel backdrop-blur">
          <div className="flex flex-col gap-5 lg:flex-row lg:items-end lg:justify-between">
            <div>
              <div className="mb-3 inline-flex items-center gap-2 rounded-full border border-line bg-white/60 px-3 py-1 text-xs font-semibold uppercase tracking-[0.22em] text-muted">
                <FlaskConical className="h-3.5 w-3.5" /> Matrix-AutoLab
              </div>
              <h1 className="font-display text-4xl font-black tracking-tight md:text-6xl">
                实验飞行记录仪
              </h1>
              <p className="mt-3 max-w-3xl text-base leading-7 text-muted">
                在插件内可视化论文复现、方法实现阶段、训练轨迹、失败记录、阶段报告、实验产物以及未来数据同步准备状态。
              </p>
            </div>
            <nav className="grid grid-cols-2 gap-2 text-sm font-semibold md:grid-cols-4">
              <Link className="rounded-2xl border border-line bg-white/70 px-4 py-3" href="/">
                <Activity className="mb-2 h-4 w-4 text-research" /> 总览
              </Link>
              <a className="rounded-2xl border border-line bg-white/70 px-4 py-3" href="#runs">
                <GitBranch className="mb-2 h-4 w-4 text-data" /> 实验记录
              </a>
              <a className="rounded-2xl border border-line bg-white/70 px-4 py-3" href="#metrics">
                <Gauge className="mb-2 h-4 w-4 text-warn" /> 指标曲线
              </a>
              <a className="rounded-2xl border border-line bg-white/70 px-4 py-3" href="#sync">
                <DatabaseZap className="mb-2 h-4 w-4 text-danger" /> 数据同步
              </a>
            </nav>
          </div>
          <div className="mt-6 flex items-center gap-2 rounded-2xl bg-ink px-4 py-3 text-sm text-white">
            <ShieldCheck className="h-4 w-4 text-data" /> 本地优先模式：当前面板只读取项目文件，不会上传任何数据。
          </div>
        </header>
        {children}
      </div>
    </main>
  );
}
