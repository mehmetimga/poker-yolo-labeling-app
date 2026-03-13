import { Routes, Route } from "react-router-dom";
import ProtectedRoute from "./components/ProtectedRoute";
import LoginPage from "./pages/LoginPage";
import ProjectListPage from "./pages/ProjectListPage";
import ProjectPage from "./pages/ProjectPage";
import TrainingPage from "./pages/TrainingPage";
import AdminPage from "./pages/AdminPage";
import ReviewPage from "./pages/ReviewPage";
import DashboardPage from "./pages/DashboardPage";

export default function App() {
  return (
    <div className="min-h-screen bg-gray-900 text-gray-100">
      <Routes>
        <Route path="/login" element={<LoginPage />} />
        <Route
          path="/"
          element={
            <ProtectedRoute>
              <ProjectListPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:projectId"
          element={
            <ProtectedRoute>
              <ProjectPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:projectId/training"
          element={
            <ProtectedRoute roles={["admin"]}>
              <TrainingPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:projectId/review"
          element={
            <ProtectedRoute roles={["admin", "reviewer"]}>
              <ReviewPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/projects/:projectId/dashboard"
          element={
            <ProtectedRoute roles={["admin", "reviewer"]}>
              <DashboardPage />
            </ProtectedRoute>
          }
        />
        <Route
          path="/admin"
          element={
            <ProtectedRoute roles={["admin"]}>
              <AdminPage />
            </ProtectedRoute>
          }
        />
      </Routes>
    </div>
  );
}
