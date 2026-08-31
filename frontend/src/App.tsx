import { Navigate, Route, Routes } from "react-router-dom";
import Landing from "@/pages/Landing";
import UseCases from "@/pages/UseCases";
import AppShell from "@/pages/AppShell";
import ProjectsPage from "@/pages/ProjectsPage";
import ProjectPage from "@/pages/ProjectPage";
import PlaylistPage from "@/pages/PlaylistPage";
import ScenarioEditorPage from "@/pages/ScenarioEditorPage";

export default function App() {
  return (
    <Routes>
      <Route path="/" element={<Landing />} />
      <Route path="/use-cases" element={<UseCases />} />
      <Route path="/app" element={<AppShell />}>
        <Route index element={<Navigate to="projects" replace />} />
        <Route path="projects" element={<ProjectsPage />} />
        <Route path="projects/:projectId" element={<ProjectPage />} />
        <Route path="playlists/:playlistId" element={<PlaylistPage />} />
        <Route path="scenarios/:scenarioId" element={<ScenarioEditorPage />} />
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
