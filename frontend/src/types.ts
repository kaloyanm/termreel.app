export interface Project {
  id: string;
  name: string;
  description: string;
  created_at: string;
  playlist_count: number;
}

export interface Playlist {
  id: string;
  project_id: string;
  name: string;
  description: string;
  created_at: string;
  scenario_count: number;
}

export interface DockerConfig {
  image: string;
  container_name: string;
  mount_host_path: string;
  mount_container_path: string;
  workdir?: string;
}

export interface TypingConfig {
  base_cps: number;
  jitter_pct: number;
  default_pause_after: number;
}

export type StepType = "command" | "comment" | "write_file";

export interface ScenarioStep {
  type: StepType;
  text?: string;
  path?: string;
  content?: string;
  pause_after?: number;
}

export interface RenderJob {
  id: string;
  scenario_id: string;
  status: "queued" | "running" | "done" | "failed";
  theme: string;
  error?: string | null;
  cast_url?: string | null;
  gif_url?: string | null;
  mp4_url?: string | null;
  created_at: string;
  started_at?: string | null;
  finished_at?: string | null;
}

export interface Scenario {
  id: string;
  playlist_id: string;
  title: string;
  docker: DockerConfig;
  typing: TypingConfig;
  steps: ScenarioStep[];
  created_at: string;
  updated_at: string;
  latest_job?: RenderJob | null;
}
