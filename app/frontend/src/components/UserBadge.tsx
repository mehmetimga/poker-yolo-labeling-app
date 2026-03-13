import { useAuthStore } from "@/stores/authStore";
import { useLogout } from "@/api/auth";

const roleBg: Record<string, string> = {
  admin: "bg-red-500/15 text-red-400 border-red-500/30",
  reviewer: "bg-yellow-500/15 text-yellow-400 border-yellow-500/30",
  labeler: "bg-green-500/15 text-green-400 border-green-500/30",
};

export default function UserBadge() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  if (!user) return null;

  const initial = user.username.charAt(0).toUpperCase();

  return (
    <div className="flex items-center gap-2">
      {/* Avatar */}
      <div className="w-7 h-7 rounded-full bg-gray-600 flex items-center justify-center text-xs font-bold text-white">
        {initial}
      </div>

      {/* Username + role */}
      <div className="flex items-center gap-1.5">
        <span className="text-sm font-medium text-gray-200">{user.username}</span>
        <span
          className={`text-[10px] px-1.5 py-0.5 rounded border font-medium ${roleBg[user.role] || "bg-gray-500/15 text-gray-400 border-gray-500/30"}`}
        >
          {user.role}
        </span>
      </div>

      {/* Logout */}
      <button
        onClick={logout}
        className="ml-1 w-7 h-7 flex items-center justify-center rounded hover:bg-gray-700 text-gray-500 hover:text-gray-300 transition-colors"
        title="Logout"
      >
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
          <path d="M9 21H5a2 2 0 0 1-2-2V5a2 2 0 0 1 2-2h4" />
          <polyline points="16 17 21 12 16 7" />
          <line x1="21" y1="12" x2="9" y2="12" />
        </svg>
      </button>
    </div>
  );
}
