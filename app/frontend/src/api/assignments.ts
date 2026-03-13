import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";

export function useAssignImages(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { image_ids: number[]; user_id: number }) => {
      const { data } = await api.post(
        `/projects/${projectId}/assignments`,
        body
      );
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["assignments"] });
    },
  });
}

export function useProjectAssignments(projectId: number | null) {
  return useQuery({
    queryKey: ["assignments", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}/assignments`);
      return data as {
        image_id: number;
        user_id: number;
        username: string;
        assigned_at: string;
      }[];
    },
    enabled: !!projectId,
  });
}

export function useMyAssignments() {
  return useQuery({
    queryKey: ["my-assignments"],
    queryFn: async () => {
      const { data } = await api.get("/users/me/assignments");
      return data as { image_id: number; assigned_at: string }[];
    },
  });
}
