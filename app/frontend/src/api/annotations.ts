import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type { Annotation, AnnotationCreate } from "@/types";

export function useAnnotations(imageId: number | null) {
  return useQuery<Annotation[]>({
    queryKey: ["annotations", imageId],
    queryFn: async () => {
      const { data } = await api.get(`/images/${imageId}/annotations`);
      return data;
    },
    enabled: !!imageId,
  });
}

export function useSaveAnnotations(imageId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (annotations: AnnotationCreate[]) => {
      const { data } = await api.put(`/images/${imageId}/annotations`, {
        annotations,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["annotations", imageId] });
      queryClient.invalidateQueries({ queryKey: ["images"] });
      queryClient.invalidateQueries({ queryKey: ["templates-status"] });
    },
  });
}

export function useAutosaveAnnotations(imageId: number) {
  return useMutation({
    mutationFn: async (annotations: AnnotationCreate[]) => {
      const { data } = await api.post(
        `/images/${imageId}/annotations/autosave`,
        { annotations }
      );
      return data;
    },
  });
}
