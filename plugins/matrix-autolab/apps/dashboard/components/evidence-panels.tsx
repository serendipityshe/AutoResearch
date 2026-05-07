import { AlertTriangle, FileText, LockKeyhole, UploadCloud } from "lucide-react";
import type { ErrorRecordView, ReportRecordView } from "@/lib/types";
import { formatDate } from "@/lib/utils";

export function FailureLedger({ errors }: { errors: ErrorRecordView[] }) {
  return (
    <section className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-muted">失败账本</p>
          <h2 className="font-display text-3xl font-black">有价值的负结果</h2>
        </div>
        <AlertTriangle className="h-7 w-7 text-warn" />
      </div>
      <div className="grid gap-3">
        {errors.length === 0 ? <p className="rounded-3xl border border-dashed border-line bg-white/50 p-5 text-muted">暂无失败记录。</p> : null}
        {errors.slice(0, 5).map((error, index) => (
          <article key={`${error.timestamp}-${index}`} className="rounded-3xl border border-line bg-white/72 p-4">
            <div className="text-xs font-bold uppercase tracking-[0.16em] text-danger">{error.severity || "错误"} / {error.category || "未分类"}</div>
            <p className="mt-2 font-bold">{error.message}</p>
            <p className="mt-2 text-sm text-muted">{error.suggestedNextStep || "暂无恢复建议。"}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function ReportLibrary({ reports }: { reports: ReportRecordView[] }) {
  return (
    <section className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-muted">报告库</p>
          <h2 className="font-display text-3xl font-black">实验依据索引</h2>
        </div>
        <FileText className="h-7 w-7 text-research" />
      </div>
      <div className="grid gap-3">
        {reports.length === 0 ? <p className="rounded-3xl border border-dashed border-line bg-white/50 p-5 text-muted">暂无报告索引。</p> : null}
        {reports.slice(0, 6).map((report, index) => (
          <article key={`${report.path}-${index}`} className="rounded-3xl border border-line bg-white/72 p-4">
            <p className="text-xs font-bold uppercase tracking-[0.16em] text-muted">{report.type}</p>
            <h3 className="mt-1 font-black">{report.title || report.path}</h3>
            <p className="mt-2 text-sm text-muted">{report.phase || "通用"} / {formatDate(report.updatedAt || report.createdAt)}</p>
          </article>
        ))}
      </div>
    </section>
  );
}

export function SyncReadiness() {
  return (
    <section id="sync" className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-muted">同步准备</p>
          <h2 className="font-display text-3xl font-black">未来上传边界</h2>
        </div>
        <UploadCloud className="h-7 w-7 text-data" />
      </div>
      <div className="grid gap-3 md:grid-cols-3">
        <div className="rounded-3xl border border-line bg-white/72 p-4">
          <LockKeyhole className="mb-3 h-5 w-5 text-danger" />
          <h3 className="font-black">默认仅本地</h3>
          <p className="mt-2 text-sm text-muted">源码、checkpoint、数据集、密钥、完整日志和本地绝对路径默认只保留在本地。</p>
        </div>
        <div className="rounded-3xl border border-line bg-white/72 p-4">
          <h3 className="font-black text-warn">上传前需审查</h3>
          <p className="mt-2 text-sm text-muted">报告正文、模型描述、日志片段和产物元数据需要用户明确确认后再考虑同步。</p>
        </div>
        <div className="rounded-3xl border border-line bg-white/72 p-4">
          <h3 className="font-black text-data">适合结构化同步</h3>
          <p className="mt-2 text-sm text-muted">Run 元信息、阶段状态、指标点、错误类别和最终分数后续可作为结构化同步载荷。</p>
        </div>
      </div>
    </section>
  );
}
