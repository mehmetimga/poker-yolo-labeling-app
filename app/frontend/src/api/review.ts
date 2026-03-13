import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";

export interface ReviewQueueItem {
  id: number;
  filename: string;
  status: string;
  assigned_schema: string | null;
  annotation_count: number;
  labeled_by: number | null;
  updated_at: string | null;
}

export interface ReviewComment {
  id: number;
  image_id: number;
  reviewer_id: number;
  reviewer_username: string;
  comment: string;
  decision: string;
  created_at: string;
}

export function useReviewQueue(projectId: number | null) {
  return useQuery<ReviewQueueItem[]>({
    queryKey: ["review-queue", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}/review-queue`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useSubmitReview(imageId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: { decision: string; comment: string }) => {
      const { data } = await api.post(`/images/${imageId}/review`, body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["review-queue"] });
      queryClient.invalidateQueries({ queryKey: ["review-comments", imageId] });
    },
  });
}

export function useReviewComments(imageId: number | null) {
  return useQuery<ReviewComment[]>({
    queryKey: ["review-comments", imageId],
    queryFn: async () => {
      const { data } = await api.get(`/images/${imageId}/review-comments`);
      return data;
    },
    enabled: !!imageId,
  });
}

export function useReviewStats(projectId: number | null) {
  return useQuery({
    queryKey: ["review-stats", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}/review-stats`);
      return data;
    },
    enabled: !!projectId,
  });
}
