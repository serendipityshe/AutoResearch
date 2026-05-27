import { CheckCircle2, CircleDashed, FileImage, FlaskConical, Layers3, TestTubeDiagonal } from "lucide-react";
import type { SkillStatusView } from "@/lib/types";
import { StatusPill } from "@/components/status-pill";

const icons = [FileImage, FlaskConical, Layers3, TestTubeDiagonal];

export function WorkflowMap({ skills }: { skills: SkillStatusView[] }) {
  return (
    <section className="rounded-[2rem] border border-line bg-panel/90 p-5 shadow-panel">
      <div className="mb-5 flex items-center justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-muted">工作流地图</p>
          <h2 className="font-display text-3xl font-black">从论文到实验的流水线</h2>
        </div>
        <CheckCircle2 className="h-8 w-8 text-data" />
      </div>
      <div className="grid gap-3 md:grid-cols-4">
        {skills.map((skill, index) => {
          const Icon = icons[index] ?? CircleDashed;
          return (
            <article key={skill.name} className="relative rounded-3xl border border-line bg-white/72 p-4">
              <div className="mb-5 flex items-start justify-between gap-3">
                <span className="rounded-2xl bg-ink p-3 text-white"><Icon className="h-5 w-5" /></span>
                <StatusPill status={skill.status} />
              </div>
              <h3 className="text-lg font-black">{skill.name}</h3>
              <p className="mt-2 min-h-10 text-sm text-muted">{skill.currentPhase || skill.report || "等待记录阶段证据。"}</p>
              <div className="mt-4 text-xs font-semibold text-muted">
                {skill.userConfirmed ? "用户已确认" : "尚未记录确认"}
              </div>
            </article>
          );
        })}
      </div>
    </section>
  );
}
