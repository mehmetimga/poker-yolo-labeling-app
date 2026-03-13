import { Routes, Route } from "react-router-dom";
import ProjectListPage from "./pages/ProjectListPage";
import ProjectPage from "./pages/ProjectPage";
import TrainingPage from "./pages/TrainingPage";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Routes>
        <Route path="/" element={<ProjectListPage />} />
        <Route path="/projects/:projectId" element={<ProjectPage />} />
        <Route path="/projects/:projectId/training" element={<TrainingPage />} />
      </Routes>
    </div>
  );
}
