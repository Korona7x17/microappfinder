/**
 * Shared TypeScript types for MicroAppFinder
 */

export type Source = "reddit" | "hn" | "producthunt" | "indiehackers";
export type Frequency = "daily" | "weekly" | "irregular";
export type WTPHint = "none" | "low" | "medium" | "high";
export type RunStatus = "pending" | "running" | "done" | "failed";

export interface Signal {
  id: string;
  run_id: string;
  source: Source;
  url: string;
  audience_guess: string;
  job_to_be_done: string;
  pain_snippet: string;
  frequency: Frequency;
  evidence_pull: boolean;
  workaround?: string;
  wtp_hint: WTPHint;
  metrics: Record<string, any>;
  confidence: number;
  micro_fit: boolean;
  created_at: string;
}

export interface Cluster {
  id: string;
  run_id: string;
  theme: string;
  audiences: string[];
  signals_count: number;
  pain_intensity_avg: number;
  frequency_mode: string;
  pull_evidence: string;
  gap_summary: string;
  score_int: number;
  created_at: string;
}

export interface Brief {
  id: string;
  run_id: string;
  cluster_id: string;
  name: string;
  who_hurts: string;
  job_to_be_done: string;
  killer_feature: string;
  scope: {
    screens: string[];
    build_time: string;
  };
  mechanics: {
    input: string;
    process: string;
    output: string;
  };
  success_metric: string;
  pricing_hint: string;
  risks: string;
  validation_plan: Record<string, any>;
  proof_urls: string[];
  created_at: string;
}

export interface Run {
  id: string;
  user_id: string;
  topic_tags: string[];
  status: RunStatus;
  started_at?: string;
  finished_at?: string;
  counters: Record<string, number>;
  cost_estimate_cents: number;
  created_at: string;
}
