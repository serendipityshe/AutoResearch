export type Status = "pending" | "in_progress" | "blocked" | "failed" | "completed" | "skipped" | "aborted" | "unknown";

export type SkillStatusView = {
  name: string;
  status: Status;
  userConfirmed: boolean;
  currentPhase: string;
  report: string;
  updatedAt: string;
};

export type ProjectSummary = {
  initialized: boolean;
  projectId: string;
  name: string;
  paperSource: string;
  taskType: string;
  datasetName: string;
  activeRunId: string;
  warnings: string[];
};

export type RunSummary = {
  runId: string;
  kind: string;
  status: Status;
  startedAt: string;
  endedAt: string;
  entrySkill: string;
  paperSource: string;
  gitBranch: string;
  gitCommit: string;
  gitDirty: boolean;
  summary: string;
  counts: {
    events: number;
    metrics: number;
    errors: number;
    artifacts: number;
    reports: number;
    changedFiles: number;
  };
};

export type EventRecordView = {
  timestamp: string;
  level: string;
  skill: string;
  phase: string;
  eventType: string;
  message: string;
};

export type MetricPointView = {
  timestamp: string;
  source: string;
  phase: string;
  step: number | null;
  epoch: number | null;
  split: string;
  name: string;
  value: number;
  unit: string;
};

export type ErrorRecordView = {
  timestamp: string;
  skill: string;
  phase: string;
  severity: string;
  category: string;
  message: string;
  suggestedNextStep: string;
};

export type ArtifactRecordView = {
  id: string;
  type: string;
  path: string;
  exists: boolean;
  sizeBytes: number;
  phase: string;
  description: string;
};

export type ReportRecordView = {
  type: string;
  phase: string;
  path: string;
  title: string;
  createdAt: string;
  updatedAt: string;
};

export type ChangedFileRecordView = {
  path: string;
  oldPath?: string;
  status: string;
  summary: string;
};

export type RunDetail = RunSummary & {
  events: EventRecordView[];
  metrics: MetricPointView[];
  errors: ErrorRecordView[];
  artifacts: ArtifactRecordView[];
  reports: ReportRecordView[];
  changedFiles: ChangedFileRecordView[];
};

export type DashboardData = {
  project: ProjectSummary;
  skills: SkillStatusView[];
  runs: RunSummary[];
  activeRun: RunDetail | null;
  legacyReports: ReportRecordView[];
};
