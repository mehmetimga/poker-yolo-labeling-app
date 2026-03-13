import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type { ImageRecord } from "@/types";
import { useAuthStore } from "@/stores/authStore";

export function useImages(
  projectId: number | null,
  filters?: { status?: string; schema?: string; sort?: string }
) {
  return useQuery<ImageRecord[]>({
    queryKey: ["images", projectId, filters],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (filters?.status) params.status = filters.status;
      if (filters?.schema) params.schema = filters.schema;
      if (filters?.sort) params.sort = filters.sort;
      const { data } = await api.get(`/projects/${projectId}/images`, {
        params,
      });
      return data;
    },
    enabled: !!projectId,
  });
}

export function useImage(imageId: number | null) {
  return useQuery<ImageRecord>({
    queryKey: ["image", imageId],
    queryFn: async () => {
      const { data } = await api.get(`/images/${imageId}`);
      return data;
    },
    enabled: !!imageId,
  });
}

export function getImageFileUrl(imageId: number): string {
  const token = useAuthStore.getState().token;
  const url = `/api/images/${imageId}/file`;
  return token ? `${url}?token=${encodeURIComponent(token)}` : url;
}

export function useUpdateImageStatus(imageId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (status: string) => {
      const { data } = await api.patch(`/images/${imageId}/status`, { status });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["images"] });
      queryClient.invalidateQueries({ queryKey: ["image", imageId] });
    },
  });
}

export function useBatchUpdateStatus(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { image_ids: number[]; status: string }) => {
      const { data } = await api.patch(
        `/projects/${projectId}/images/batch-status`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useBatchAssignSchema(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { image_ids: number[]; schema_name: string }) => {
      const { data } = await api.post(
        `/projects/${projectId}/images/batch-schema`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useRunInference(imageId: number) {
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/images/${imageId}/infer`);
      return data;
    },
  });
}

export function useBatchInference(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body?: { image_ids?: number[]; confidence?: number }) => {
      const { data } = await api.post(`/projects/${projectId}/batch-infer`, body || {});
      return data as { task_id: string | null; total_images: number };
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useTaskStatus(taskId: string | null) {
  return useQuery<{ task_id: string; status: string; total: number; completed: number; errors: number }>({
    queryKey: ["task", taskId],
    queryFn: async () => {
      const { data } = await api.get(`/tasks/${taskId}`);
      return data;
    },
    enabled: !!taskId,
    refetchInterval: (query) => {
      if (query.state.data?.status === "done") return false;
      return 2000;
    },
  });
}
