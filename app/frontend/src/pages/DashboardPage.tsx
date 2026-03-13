import { useNavigate, useParams } from "react-router-dom";
import { useProjectDashboard, useMyProgress } from "@/api/dashboard";
import UserBadge from "@/components/UserBadge";

export default function DashboardPage() {
  const { projectId } = useParams();
  const pid = projectId ? parseInt(projectId) : null;
  const navigate = useNavigate();
  const { data: dashboard, isLoading } = useProjectDashboard(pid);
  const { data: myProgress } = useMyProgress();

  return (
    <div className="min-h-screen flex flex-col">
      {/* Top bar */}
      <div className="bg-gray-800 border-b border-gray-700 px-6 py-3 flex items-center justify-between shrink-0">
        <div className="flex items-center gap-3">
          <button
            onClick={() => navigate(`/projects/${projectId}`)}
            className="flex items-center gap-1 text-sm text-gray-400 hover:text-white bg-gray-700/50 hover:bg-gray-700 px-2.5 py-1 rounded transition-colors"
          >
            <svg width="14" height="14" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round"><path d="M15 18l-6-6 6-6"/></svg>
            Back
          </button>
          <div className="w-px h-5 bg-gray-700" />
          <h1 className="text-lg font-bold">Dashboard</h1>
        </div>
        <UserBadge />
      </div>

      <div className="max-w-5xl w-full mx-auto p-6 flex-1">

      {isLoading && <p className="text-gray-400 text-sm">Loading...</p>}

      {/* My Progress */}
      {myProgress && (
        <div className="bg-gray-800 rounded-lg p-5 mb-6">
          <h2 className="text-lg font-semibold mb-3">My Progress</h2>
          <div className="grid grid-cols-3 gap-4">
            <StatCard label="Assigned" value={myProgress.assigned} />
            <StatCard label="Labeled" value={myProgress.labeled} />
            <StatCard label="Reviewed" value={myProgress.reviewed} />
          </div>
        </div>
      )}

      {/* Project Overview */}
      {dashboard && (
        <>
          <div className="grid grid-cols-3 gap-4 mb-6">
            <StatCard label="Total Images" value={dashboard.total_images} />
            <StatCard
              label="Approved"
              value={dashboard.approved}
              color="text-green-400"
            />
            <StatCard
              label="Rejected"
              value={dashboard.rejected}
              color="text-red-400"
            />
          </div>

          {/* Approval Rate Bar */}
          {dashboard.total_images > 0 && (
            <div className="bg-gray-800 rounded-lg p-5 mb-6">
              <h3 className="text-sm text-gray-400 mb-2">Approval Rate</h3>
              <div className="w-full h-4 bg-gray-700 rounded-full overflow-hidden flex">
                <div
                  className="bg-green-600 h-full"
                  style={{
                    width: `${(dashboard.approved / dashboard.total_images) * 100}%`,
                  }}
                />
                <div
                  className="bg-red-600 h-full"
                  style={{
                    width: `${(dashboard.rejected / dashboard.total_images) * 100}%`,
                  }}
                />
              </div>
              <div className="flex justify-between text-xs text-gray-400 mt-1">
                <span>
                  {Math.round(
                    (dashboard.approved / dashboard.total_images) * 100
                  )}
                  % approved
                </span>
                <span>
                  {dashboard.total_images - dashboard.approved - dashboard.rejected}{" "}
                  pending
                </span>
              </div>
            </div>
          )}

          {/* Per-User Table */}
          <div className="bg-gray-800 rounded-lg p-5">
            <h2 className="text-lg font-semibold mb-3">Per-User Stats</h2>
            <table className="w-full text-sm">
              <thead>
                <tr className="text-left text-gray-400 border-b border-gray-700">
                  <th className="py-2">User</th>
                  <th className="py-2 text-right">Labeled</th>
                  <th className="py-2 text-right">Reviewed</th>
                </tr>
              </thead>
              <tbody>
                {dashboard.per_user.map((u) => (
                  <tr key={u.user_id} className="border-b border-gray-700">
                    <td className="py-2">{u.username}</td>
                    <td className="py-2 text-right text-blue-400">
                      {u.labeled}
                    </td>
                    <td className="py-2 text-right text-purple-400">
                      {u.reviewed}
                    </td>
                  </tr>
                ))}
                {dashboard.per_user.length === 0 && (
                  <tr>
                    <td colSpan={3} className="py-4 text-gray-500 text-center">
                      No activity yet
                    </td>
                  </tr>
                )}
              </tbody>
            </table>
          </div>
        </>
      )}
      </div>
    </div>
  );
}

function StatCard({
  label,
  value,
  color = "text-white",
}: {
  label: string;
  value: number;
  color?: string;
}) {
  return (
    <div className="bg-gray-800 rounded-lg p-4 border border-gray-700">
      <p className="text-xs text-gray-400 mb-1">{label}</p>
      <p className={`text-2xl font-bold ${color}`}>{value}</p>
    </div>
  );
}
