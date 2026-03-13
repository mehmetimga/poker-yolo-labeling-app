import { useQuery } from "@tanstack/react-query";
import api from "./client";

export interface DashboardData {
  total_images: number;
  approved: number;
  rejected: number;
  per_user: {
    user_id: number;
    username: string;
    labeled: number;
    reviewed: number;
  }[];
}

export interface MyProgress {
  user_id: number;
  username: string;
  role: string;
  labeled: number;
  reviewed: number;
  assigned: number;
}

export function useProjectDashboard(projectId: number | null) {
  return useQuery<DashboardData>({
    queryKey: ["project-dashboard", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}/dashboard`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useMyProgress() {
  return useQuery<MyProgress>({
    queryKey: ["my-progress"],
    queryFn: async () => {
      const { data } = await api.get("/users/me/progress");
      return data;
    },
  });
}

export interface AuditLogEntry {
  id: number;
  user_id: number | null;
  action: string;
  entity_type: string;
  entity_id: number;
  detail_json: string | null;
  created_at: string;
}

export function useAuditLog(params?: {
  user_id?: number;
  action?: string;
  limit?: number;
}) {
  return useQuery<AuditLogEntry[]>({
    queryKey: ["audit-log", params],
    queryFn: async () => {
      const { data } = await api.get("/audit-log", { params });
      return data;
    },
  });
}
