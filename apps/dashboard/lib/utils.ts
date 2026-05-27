import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
  return twMerge(clsx(inputs));
}

export function formatDate(value: string) {
  if (!value) return "未记录";
  const date = new Date(value);
  if (Number.isNaN(date.getTime())) return value;
  return new Intl.DateTimeFormat("zh-CN", {
    month: "short",
    day: "2-digit",
    hour: "2-digit",
    minute: "2-digit",
  }).format(date);
}

export function compactId(value: string, size = 10) {
  if (!value) return "暂无";
  if (value.length <= size) return value;
  return `${value.slice(0, size)}...`;
}

export function statusLabel(value: string) {
  const labels: Record<string, string> = {
    pending: "待开始",
    in_progress: "进行中",
    blocked: "已阻塞",
    failed: "失败",
    completed: "已完成",
    skipped: "已跳过",
    aborted: "已中止",
    unknown: "未知",
  };
  return labels[value] ?? (value.replace(/_/g, " ") || "未知");
}
