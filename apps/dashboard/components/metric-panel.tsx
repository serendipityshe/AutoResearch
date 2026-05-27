"use client";

import { Line, LineChart, ResponsiveContainer, Tooltip, XAxis, YAxis } from "recharts";
import type { MetricPointView } from "@/lib/types";

export function MetricPanel({ metrics }: { metrics: MetricPointView[] }) {
  const primaryName = metrics[0]?.name ?? "指标";
  const chartData = metrics.slice(-80).map((item, index) => ({
    index: item.step ?? item.epoch ?? index + 1,
    value: item.value,
    name: item.name,
  }));
  return (
    <section id="metrics" className="rounded-[2rem] border border-line bg-ink p-5 text-white shadow-panel">
      <div className="mb-5 flex items-end justify-between">
        <div>
          <p className="text-xs font-bold uppercase tracking-[0.22em] text-white/55">指标控制台</p>
          <h2 className="font-display text-3xl font-black">训练信号</h2>
        </div>
        <span className="rounded-full bg-white/10 px-3 py-1 text-sm font-bold">{metrics.length} 个点</span>
      </div>
      <div className="h-72 rounded-3xl border border-white/10 bg-white/5 p-4">
        {chartData.length === 0 ? (
          <div className="flex h-full items-center justify-center text-white/55">暂无指标记录。失败实验和负结果一旦被记录，也会显示在这里。</div>
        ) : (
          <ResponsiveContainer width="100%" height="100%">
            <LineChart data={chartData}>
              <XAxis dataKey="index" stroke="rgba(255,255,255,.45)" />
              <YAxis stroke="rgba(255,255,255,.45)" />
              <Tooltip contentStyle={{ background: "#111827", border: "1px solid rgba(255,255,255,.2)", borderRadius: 16 }} />
              <Line type="monotone" dataKey="value" name={primaryName} stroke="#10b981" strokeWidth={3} dot={false} />
            </LineChart>
          </ResponsiveContainer>
        )}
      </div>
    </section>
  );
}
