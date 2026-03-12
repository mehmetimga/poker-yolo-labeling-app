import { useQuery } from "@tanstack/react-query";
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
