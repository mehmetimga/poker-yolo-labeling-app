import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type { ImageRecord } from "@/types";

export function useImages(
  projectId: number | null,
  filters?: { status?: string; schema?: string }
) {
  return useQuery<ImageRecord[]>({
    queryKey: ["images", projectId, filters],
    queryFn: async () => {
      const params: Record<string, string> = {};
      if (filters?.status) params.status = filters.status;
      if (filters?.schema) params.schema = filters.schema;
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
  return `/api/images/${imageId}/file`;
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
