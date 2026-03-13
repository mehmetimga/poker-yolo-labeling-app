import { useState } from "react";
import { useNavigate } from "react-router-dom";
import { useProjects, useCreateProject } from "@/api/projects";
import { useAuthStore } from "@/stores/authStore";
import UserBadge from "@/components/UserBadge";

export default function ProjectListPage() {
  const navigate = useNavigate();
  const { data: projects, isLoading } = useProjects();
  const createProject = useCreateProject();
  const user = useAuthStore((s) => s.user);

  const [showForm, setShowForm] = useState(false);
  const [name, setName] = useState("");
  const [description, setDescription] = useState("");
  const [imagePath, setImagePath] = useState("");

  const handleCreate = async () => {
    if (!name || !imagePath) return;
    const project = await createProject.mutateAsync({
      name,
      description,
      image_root_path: imagePath,
    });
    setShowForm(false);
    setName("");
    setDescription("");
    setImagePath("");
    navigate(`/projects/${project.id}`);
  };

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between shrink-0">
        <h1 className="text-lg font-bold">Poker YOLO Labeling</h1>
        <div className="flex items-center gap-3">
          {user?.role === "admin" && (
            <button
              onClick={() => setShowForm(true)}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded text-sm font-medium transition-colors"
            >
              + New Project
            </button>
          )}
          <div className="w-px h-6 bg-gray-700" />
          <UserBadge />
        </div>
      </div>

      <div className="max-w-4xl w-full mx-auto p-8 flex-1">

      {showForm && (
        <div className="bg-gray-800 rounded-lg p-6 mb-6">
          <h2 className="text-xl font-semibold mb-4">Create Project</h2>
          <div className="space-y-3">
            <input
              placeholder="Project name"
              value={name}
              onChange={(e) => setName(e.target.value)}
              className="w-full bg-gray-700 rounded px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              placeholder="Description (optional)"
              value={description}
              onChange={(e) => setDescription(e.target.value)}
              className="w-full bg-gray-700 rounded px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            <input
              placeholder="Image folder path (absolute)"
              value={imagePath}
              onChange={(e) => setImagePath(e.target.value)}
              className="w-full bg-gray-700 rounded px-3 py-2 outline-none focus:ring-2 focus:ring-blue-500"
            />
            <div className="flex gap-2">
              <button
                onClick={handleCreate}
                disabled={!name || !imagePath}
                className="bg-green-600 hover:bg-green-700 disabled:opacity-50 px-4 py-2 rounded font-medium"
              >
                Create
              </button>
              <button
                onClick={() => setShowForm(false)}
                className="bg-gray-600 hover:bg-gray-500 px-4 py-2 rounded"
              >
                Cancel
              </button>
            </div>
          </div>
        </div>
      )}

      {isLoading && <p className="text-gray-400">Loading projects...</p>}

      <div className="grid gap-4">
        {projects?.map((project) => (
          <div
            key={project.id}
            onClick={() => navigate(`/projects/${project.id}`)}
            className="bg-gray-800 hover:bg-gray-750 rounded-lg p-5 cursor-pointer border border-gray-700 hover:border-gray-500 transition"
          >
            <h3 className="text-lg font-semibold">{project.name}</h3>
            {project.description && (
              <p className="text-gray-400 text-sm mt-1">
                {project.description}
              </p>
            )}
            <div className="flex gap-4 mt-2 text-sm text-gray-500">
              <span>{project.image_count} images</span>
              <span>{project.image_root_path}</span>
            </div>
          </div>
        ))}
        {projects?.length === 0 && !isLoading && (
          <p className="text-gray-500">
            No projects yet. Create one to get started.
          </p>
        )}
      </div>
      </div>
    </div>
  );
}
