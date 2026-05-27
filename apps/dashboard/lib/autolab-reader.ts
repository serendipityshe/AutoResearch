import { promises as fs } from "fs";
import path from "path";
import type {
  ArtifactRecordView,
  ChangedFileRecordView,
  DashboardData,
  ErrorRecordView,
  EventRecordView,
  MetricPointView,
  ProjectSummary,
  ReportRecordView,
  RunDetail,
  RunSummary,
  SkillStatusView,
  Status,
} from "@/lib/types";

const DASHBOARD_ROOT = process.env.AUTOLAB_DASHBOARD_ROOT ?? process.cwd();
const PLUGIN_ROOT = path.resolve(DASHBOARD_ROOT, "..", "..");
const PROJECT_ROOT = path.resolve(process.env.AUTOLAB_PROJECT_ROOT ?? path.resolve(PLUGIN_ROOT, "..", ".."));
const AUTOLAB_ROOT = path.join(PROJECT_ROOT, ".autolab");

type JsonObject = Record<string, unknown>;

async function pathExists(filePath: string) {
  try {
    await fs.access(filePath);
    return true;
  } catch {
    return false;
  }
}

async function readJson<T>(filePath: string, fallback: T, warnings: string[]) {
  if (!(await pathExists(filePath))) return fallback;
  try {
    return JSON.parse(await fs.readFile(filePath, "utf8")) as T;
  } catch (error) {
    warnings.push(`无法解析 ${path.relative(PROJECT_ROOT, filePath)}：${String(error)}`);
    return fallback;
  }
}

async function readJsonl(filePath: string, warnings: string[]) {
  if (!(await pathExists(filePath))) return [] as JsonObject[];
  const text = await fs.readFile(filePath, "utf8");
  const records: JsonObject[] = [];
  for (const [index, line] of text.split(/\r?\n/).entries()) {
    if (!line.trim()) continue;
    try {
      records.push(JSON.parse(line) as JsonObject);
    } catch {
      warnings.push(`已跳过 ${path.relative(PROJECT_ROOT, filePath)} 中第 ${index + 1} 行异常 JSONL`);
    }
  }
  return records;
}

function text(value: unknown) {
  return typeof value === "string" ? value : "";
}

function bool(value: unknown) {
  return typeof value === "boolean" ? value : false;
}

function numberOrNull(value: unknown) {
  return typeof value === "number" && Number.isFinite(value) ? value : null;
}

function status(value: unknown): Status {
  const known = ["pending", "in_progress", "blocked", "failed", "completed", "skipped", "aborted"];
  return typeof value === "string" && known.includes(value) ? (value as Status) : "unknown";
}

async function readProject(warnings: string[]): Promise<ProjectSummary> {
  const project = await readJson<JsonObject | null>(path.join(AUTOLAB_ROOT, "project.json"), null, warnings);
  const workflow = await readJson<JsonObject | null>(path.join(AUTOLAB_ROOT, "workflow_status.json"), null, warnings);
  const legacyWorkflow = await readJson<JsonObject | null>(path.join(PROJECT_ROOT, "workflow_status.json"), null, warnings);
  if (!project && legacyWorkflow) {
    warnings.push("正在使用旧版工作流文件；当前项目尚未初始化 .autolab。需要实验历史时请先初始化本地记录。");
  }
  if (!project && !legacyWorkflow) {
    warnings.push("未发现 .autolab 项目记录。初始化本地记录后可解锁实验历史视图。");
  }
  const dataset = (project?.dataset ?? {}) as JsonObject;
  return {
    initialized: Boolean(project),
    projectId: text(project?.project_id),
    name: text(project?.name) || "Matrix-AutoLab 项目",
    paperSource: text(project?.paper_source) || "main.tex",
    taskType: text(project?.task_type) || "未知",
    datasetName: text(dataset.name),
    activeRunId: text(workflow?.active_run_id),
    warnings,
  };
}

async function readSkills(warnings: string[]): Promise<SkillStatusView[]> {
  const workflow = await readJson<JsonObject | null>(path.join(AUTOLAB_ROOT, "workflow_status.json"), null, warnings);
  const legacyWorkflow = await readJson<JsonObject | null>(path.join(PROJECT_ROOT, "workflow_status.json"), null, warnings);
  const source = ((workflow?.skills ?? legacyWorkflow?.skills) ?? {}) as Record<string, JsonObject>;
  const names = ["matrix-autolab", "paperbanana", "autolab", "autobaseline"];
  return names.map((name) => {
    const item = source[name] ?? {};
    return {
      name,
      status: status(item.status),
      userConfirmed: bool(item.user_confirmed),
      currentPhase: text(item.current_phase),
      report: text(item.report),
      updatedAt: text(item.updated_at) || text(item.timestamp),
    };
  });
}

async function countJsonl(filePath: string) {
  if (!(await pathExists(filePath))) return 0;
  const text = await fs.readFile(filePath, "utf8");
  return text.split(/\r?\n/).filter(Boolean).length;
}

async function readRunSummary(runDir: string, warnings: string[]): Promise<RunSummary | null> {
  const run = await readJson<JsonObject | null>(path.join(runDir, "run.json"), null, warnings);
  if (!run) return null;
  const git = (run.git ?? {}) as JsonObject;
  const artifacts = await readJson<{ artifacts?: unknown[] }>(path.join(runDir, "artifacts.json"), {}, warnings);
  const changed = await readJson<{ files?: unknown[] }>(path.join(runDir, "changed_files.json"), {}, warnings);
  const reports = await readJson<{ reports?: unknown[] }>(path.join(runDir, "reports", "reports_index.json"), {}, warnings);
  return {
    runId: text(run.run_id) || path.basename(runDir),
    kind: text(run.kind),
    status: status(run.status),
    startedAt: text(run.started_at),
    endedAt: text(run.ended_at),
    entrySkill: text(run.entry_skill),
    paperSource: text(run.paper_source),
    gitBranch: text(git.branch),
    gitCommit: text(git.commit),
    gitDirty: bool(git.dirty),
    summary: text(run.summary),
    counts: {
      events: await countJsonl(path.join(runDir, "events.jsonl")),
      metrics: await countJsonl(path.join(runDir, "metrics.jsonl")),
      errors: await countJsonl(path.join(runDir, "errors.jsonl")),
      artifacts: artifacts.artifacts?.length ?? 0,
      reports: reports.reports?.length ?? 0,
      changedFiles: changed.files?.length ?? 0,
    },
  };
}

export async function getRunSummaries(warnings: string[]) {
  const runsRoot = path.join(AUTOLAB_ROOT, "runs");
  if (!(await pathExists(runsRoot))) return [] as RunSummary[];
  const entries = await fs.readdir(runsRoot, { withFileTypes: true });
  const runs = await Promise.all(
    entries.filter((entry) => entry.isDirectory()).map((entry) => readRunSummary(path.join(runsRoot, entry.name), warnings)),
  );
  return runs.filter((run): run is RunSummary => Boolean(run)).sort((a, b) => b.startedAt.localeCompare(a.startedAt));
}

export async function getRunDetail(runId: string, warnings: string[]): Promise<RunDetail | null> {
  const runDir = path.join(AUTOLAB_ROOT, "runs", runId);
  const summary = await readRunSummary(runDir, warnings);
  if (!summary) return null;
  const events = (await readJsonl(path.join(runDir, "events.jsonl"), warnings)).map<EventRecordView>((item) => ({
    timestamp: text(item.timestamp),
    level: text(item.level),
    skill: text(item.skill),
    phase: text(item.phase),
    eventType: text(item.event_type),
    message: text(item.message),
  }));
  const metrics = (await readJsonl(path.join(runDir, "metrics.jsonl"), warnings)).map<MetricPointView>((item) => ({
    timestamp: text(item.timestamp),
    source: text(item.source),
    phase: text(item.phase),
    step: numberOrNull(item.step),
    epoch: numberOrNull(item.epoch),
    split: text(item.split),
    name: text(item.name),
    value: numberOrNull(item.value) ?? 0,
    unit: text(item.unit),
  }));
  const errors = (await readJsonl(path.join(runDir, "errors.jsonl"), warnings)).map<ErrorRecordView>((item) => ({
    timestamp: text(item.timestamp),
    skill: text(item.skill),
    phase: text(item.phase),
    severity: text(item.severity),
    category: text(item.category),
    message: text(item.message),
    suggestedNextStep: text(item.suggested_next_step),
  }));
  const artifactPayload = await readJson<{ artifacts?: JsonObject[] }>(path.join(runDir, "artifacts.json"), {}, warnings);
  const artifacts = (artifactPayload.artifacts ?? []).map<ArtifactRecordView>((item) => ({
    id: text(item.id),
    type: text(item.type),
    path: text(item.path),
    exists: bool(item.exists),
    sizeBytes: numberOrNull(item.size_bytes) ?? 0,
    phase: text(item.phase),
    description: text(item.description),
  }));
  const reportPayload = await readJson<{ reports?: JsonObject[] }>(path.join(runDir, "reports", "reports_index.json"), {}, warnings);
  const reports = (reportPayload.reports ?? []).map<ReportRecordView>((item) => ({
    type: text(item.type),
    phase: text(item.phase),
    path: text(item.path),
    title: text(item.title),
    createdAt: text(item.created_at),
    updatedAt: text(item.updated_at),
  }));
  const changedPayload = await readJson<{ files?: JsonObject[] }>(path.join(runDir, "changed_files.json"), {}, warnings);
  const changedFiles = (changedPayload.files ?? []).map<ChangedFileRecordView>((item) => ({
    path: text(item.path),
    oldPath: text(item.old_path) || undefined,
    status: text(item.status),
    summary: text(item.summary),
  }));
  return { ...summary, events, metrics, errors, artifacts, reports, changedFiles };
}

async function legacyReports(): Promise<ReportRecordView[]> {
  const candidates = [
    "paperbanana_completion_report.md",
    "experiment_docs/IMPLEMENTATION_SUMMARY.md",
    "baselines/BASELINE_COMPARISON_REPORT.md",
  ];
  const reports: ReportRecordView[] = [];
  for (const item of candidates) {
    if (await pathExists(path.join(PROJECT_ROOT, item))) {
      reports.push({
        type: "legacy_report",
        phase: "",
        path: item,
        title: path.basename(item),
        createdAt: "",
        updatedAt: "",
      });
    }
  }
  return reports;
}

export async function getDashboardData(): Promise<DashboardData> {
  const warnings: string[] = [];
  const project = await readProject(warnings);
  const skills = await readSkills(warnings);
  const runs = await getRunSummaries(warnings);
  const activeRunId = project.activeRunId || runs[0]?.runId || "";
  const activeRun = activeRunId ? await getRunDetail(activeRunId, warnings) : null;
  return {
    project: { ...project, warnings },
    skills,
    runs,
    activeRun,
    legacyReports: await legacyReports(),
  };
}
