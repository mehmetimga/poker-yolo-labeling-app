import { useState } from "react";
import { useNavigate, useParams } from "react-router-dom";
import { useUsers, useCreateUser, useUpdateUser } from "@/api/users";
import { useAuditLog } from "@/api/dashboard";
import UserBadge from "@/components/UserBadge";

type Tab = "users" | "audit";

export default function AdminPage() {
  const { projectId } = useParams();
  const navigate = useNavigate();
  const [tab, setTab] = useState<Tab>("users");

  return (
    <div className="max-w-5xl mx-auto p-6">
      <div className="flex items-center justify-between mb-6">
        <div className="flex items-center gap-4">
          <button
            onClick={() => navigate(projectId ? `/projects/${projectId}` : "/")}
            className="text-gray-400 hover:text-gray-200"
          >
            Back
          </button>
          <h1 className="text-2xl font-bold">Admin</h1>
        </div>
        <UserBadge />
      </div>

      <div className="flex gap-2 mb-6">
        {(["users", "audit"] as Tab[]).map((t) => (
          <button
            key={t}
            onClick={() => setTab(t)}
            className={`px-4 py-2 rounded text-sm font-medium ${
              tab === t
                ? "bg-blue-600 text-white"
                : "bg-gray-700 text-gray-300 hover:bg-gray-600"
            }`}
          >
            {t === "users" ? "Users" : "Audit Log"}
          </button>
        ))}
      </div>

      {tab === "users" && <UsersTab />}
      {tab === "audit" && <AuditTab />}
    </div>
  );
}

function UsersTab() {
  const { data: users, isLoading } = useUsers();
  const createUser = useCreateUser();
  const updateUser = useUpdateUser();
  const [showForm, setShowForm] = useState(false);
  const [username, setUsername] = useState("");
  const [email, setEmail] = useState("");
  const [password, setPassword] = useState("");
  const [role, setRole] = useState("labeler");

  const handleCreate = () => {
    if (!username || !email || !password) return;
    createUser.mutate(
      { username, email, password, role },
      {
        onSuccess: () => {
          setShowForm(false);
          setUsername("");
          setEmail("");
          setPassword("");
          setRole("labeler");
        },
      }
    );
  };

  const roleColors: Record<string, string> = {
    admin: "text-red-400",
    reviewer: "text-yellow-400",
    labeler: "text-green-400",
  };

  return (
    <div>
      <div className="flex justify-between mb-4">
        <h2 className="text-lg font-semibold">Users</h2>
        <button
          onClick={() => setShowForm(!showForm)}
          className="bg-green-600 hover:bg-green-700 px-3 py-1.5 rounded text-sm"
        >
          + New User
        </button>
      </div>

      {showForm && (
        <div className="bg-gray-800 rounded p-4 mb-4 space-y-3">
          <input
            placeholder="Username"
            value={username}
            onChange={(e) => setUsername(e.target.value)}
            className="w-full bg-gray-700 rounded px-3 py-2 outline-none text-sm"
          />
          <input
            placeholder="Email"
            value={email}
            onChange={(e) => setEmail(e.target.value)}
            className="w-full bg-gray-700 rounded px-3 py-2 outline-none text-sm"
          />
          <input
            type="password"
            placeholder="Password"
            value={password}
            onChange={(e) => setPassword(e.target.value)}
            className="w-full bg-gray-700 rounded px-3 py-2 outline-none text-sm"
          />
          <select
            value={role}
            onChange={(e) => setRole(e.target.value)}
            className="bg-gray-700 rounded px-3 py-2 text-sm"
          >
            <option value="labeler">Labeler</option>
            <option value="reviewer">Reviewer</option>
            <option value="admin">Admin</option>
          </select>
          <div className="flex gap-2">
            <button
              onClick={handleCreate}
              className="bg-blue-600 hover:bg-blue-700 px-3 py-1.5 rounded text-sm"
            >
              Create
            </button>
            <button
              onClick={() => setShowForm(false)}
              className="bg-gray-600 hover:bg-gray-500 px-3 py-1.5 rounded text-sm"
            >
              Cancel
            </button>
          </div>
          {createUser.isError && (
            <p className="text-red-400 text-sm">
              {(createUser.error as Error)?.message || "Failed to create user"}
            </p>
          )}
        </div>
      )}

      {isLoading && <p className="text-gray-400 text-sm">Loading...</p>}

      <table className="w-full text-sm">
        <thead>
          <tr className="text-left text-gray-400 border-b border-gray-700">
            <th className="py-2">ID</th>
            <th className="py-2">Username</th>
            <th className="py-2">Email</th>
            <th className="py-2">Role</th>
            <th className="py-2">Active</th>
            <th className="py-2">Actions</th>
          </tr>
        </thead>
        <tbody>
          {users?.map((u) => (
            <tr key={u.id} className="border-b border-gray-800">
              <td className="py-2 text-gray-500">{u.id}</td>
              <td className="py-2">{u.username}</td>
              <td className="py-2 text-gray-400">{u.email}</td>
              <td className={`py-2 ${roleColors[u.role] || ""}`}>{u.role}</td>
              <td className="py-2">
                <button
                  onClick={() =>
                    updateUser.mutate({ id: u.id, is_active: !u.is_active })
                  }
                  className={`text-xs px-2 py-0.5 rounded ${
                    u.is_active
                      ? "bg-green-800 text-green-300"
                      : "bg-red-800 text-red-300"
                  }`}
                >
                  {u.is_active ? "Active" : "Inactive"}
                </button>
              </td>
              <td className="py-2">
                <select
                  value={u.role}
                  onChange={(e) =>
                    updateUser.mutate({ id: u.id, role: e.target.value })
                  }
                  className="bg-gray-700 rounded px-2 py-0.5 text-xs"
                >
                  <option value="labeler">labeler</option>
                  <option value="reviewer">reviewer</option>
                  <option value="admin">admin</option>
                </select>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
}

function AuditTab() {
  const { data: entries, isLoading } = useAuditLog({ limit: 100 });

  return (
    <div>
      <h2 className="text-lg font-semibold mb-4">Audit Log</h2>
      {isLoading && <p className="text-gray-400 text-sm">Loading...</p>}
      <div className="space-y-1 text-sm max-h-[600px] overflow-y-auto">
        {entries?.map((e) => (
          <div
            key={e.id}
            className="flex gap-3 py-1.5 border-b border-gray-800 text-gray-300"
          >
            <span className="text-gray-500 w-36 shrink-0">
              {new Date(e.created_at).toLocaleString()}
            </span>
            <span className="text-blue-400 w-16 shrink-0">
              {e.action}
            </span>
            <span className="text-gray-400">
              {e.entity_type}#{e.entity_id}
            </span>
            {e.detail_json && (
              <span className="text-gray-500 truncate">{e.detail_json}</span>
            )}
          </div>
        ))}
      </div>
    </div>
  );
}
