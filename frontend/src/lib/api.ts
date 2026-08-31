import axios from "axios";
import type { Flavour, Playlist, Project, RenderJob, Scenario } from "@/types";

export const api = axios.create({ baseURL: "/api" });

export const Flavours = {
  list: () => api.get<Flavour[]>("/flavours").then((r) => r.data),
};

export const Projects = {
  list: () => api.get<Project[]>("/projects").then((r) => r.data),
  create: (data: { name: string; description?: string }) =>
    api.post<Project>("/projects", data).then((r) => r.data),
  get: (id: string) => api.get<Project>(`/projects/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<{ name: string; description: string }>) =>
    api.patch<Project>(`/projects/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/projects/${id}`),
};

export const Playlists = {
  list: (projectId: string) =>
    api.get<Playlist[]>(`/projects/${projectId}/playlists`).then((r) => r.data),
  create: (projectId: string, data: { name: string; description?: string }) =>
    api.post<Playlist>(`/projects/${projectId}/playlists`, data).then((r) => r.data),
  get: (id: string) => api.get<Playlist>(`/playlists/${id}`).then((r) => r.data),
  remove: (id: string) => api.delete(`/playlists/${id}`),
};

export const Scenarios = {
  list: (playlistId: string) =>
    api.get<Scenario[]>(`/playlists/${playlistId}/scenarios`).then((r) => r.data),
  create: (playlistId: string, data: Omit<Scenario, "id" | "playlist_id" | "created_at" | "updated_at" | "latest_job">) =>
    api.post<Scenario>(`/playlists/${playlistId}/scenarios`, data).then((r) => r.data),
  get: (id: string) => api.get<Scenario>(`/scenarios/${id}`).then((r) => r.data),
  update: (id: string, data: Partial<Pick<Scenario, "title" | "docker" | "typing" | "steps">>) =>
    api.put<Scenario>(`/scenarios/${id}`, data).then((r) => r.data),
  remove: (id: string) => api.delete(`/scenarios/${id}`),
  yaml: (id: string) => api.get<string>(`/scenarios/${id}/yaml`, { responseType: "text" }).then((r) => r.data),
  render: (id: string, theme: string) =>
    api.post<RenderJob>(`/scenarios/${id}/render`, { theme }).then((r) => r.data),
  jobs: (id: string) => api.get<RenderJob[]>(`/scenarios/${id}/jobs`).then((r) => r.data),
};

export const Jobs = {
  get: (id: string) => api.get<RenderJob>(`/jobs/${id}`).then((r) => r.data),
  log: (id: string) => api.get<string>(`/jobs/${id}/log`, { responseType: "text" }).then((r) => r.data),
};
