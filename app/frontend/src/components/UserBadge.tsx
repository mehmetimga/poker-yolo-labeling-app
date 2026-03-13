import { useAuthStore } from "@/stores/authStore";
import { useLogout } from "@/api/auth";

const roleColors: Record<string, string> = {
  admin: "bg-red-600",
  reviewer: "bg-yellow-600",
  labeler: "bg-green-600",
};

export default function UserBadge() {
  const user = useAuthStore((s) => s.user);
  const logout = useLogout();

  if (!user) return null;

  return (
    <div className="flex items-center gap-2">
      <span className="text-sm text-gray-300">{user.username}</span>
      <span
        className={`text-xs px-2 py-0.5 rounded-full text-white ${roleColors[user.role] || "bg-gray-600"}`}
      >
        {user.role}
      </span>
      <button
        onClick={logout}
        className="text-xs text-gray-400 hover:text-gray-200 ml-1"
      >
        Logout
      </button>
    </div>
  );
}
