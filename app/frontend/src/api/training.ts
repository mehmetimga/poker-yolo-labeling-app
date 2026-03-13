import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type { TrainingRun, TrainingLiveStatus } from "@/types";

export function useTrainingRuns(projectId: number | null) {
  return useQuery<TrainingRun[]>({
    queryKey: ["training-runs", projectId],
    queryFn: async () => {
      const { data } = await api.get(`/projects/${projectId}/training-runs`);
      return data;
    },
    enabled: !!projectId,
  });
}

export function useTrainingRun(runId: number | null) {
  return useQuery<TrainingRun>({
    queryKey: ["training-run", runId],
    queryFn: async () => {
      const { data } = await api.get(`/training-runs/${runId}`);
      return data;
    },
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.status;
      if (status && !["done", "failed"].includes(status)) return 3000;
      return false;
    },
  });
}

export function useTrainingLiveStatus(runId: number | null) {
  return useQuery<TrainingLiveStatus>({
    queryKey: ["training-live-status", runId],
    queryFn: async () => {
      const { data } = await api.get(`/training-runs/${runId}/status`);
      return data;
    },
    enabled: !!runId,
    refetchInterval: (query) => {
      const status = query.state.data?.live_status;
      if (status && !["done", "failed"].includes(status)) return 2000;
      return false;
    },
  });
}

export function useCreateTrainingRun(projectId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      name: string;
      base_model?: string;
      epochs?: number;
      batch_size?: number;
      img_size?: number;
      learning_rate?: number;
      train_ratio?: number;
      val_ratio?: number;
      test_ratio?: number;
    }) => {
      const { data } = await api.post(`/projects/${projectId}/training-runs`, body);
      return data as TrainingRun;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["training-runs"] });
    },
  });
}

export function useTrainingSplits(runId: number | null) {
  return useQuery({
    queryKey: ["training-splits", runId],
    queryFn: async () => {
      const { data } = await api.get(`/training-runs/${runId}/splits`);
      return data as { summary: Record<string, number>; images: { image_id: number; split: string }[] };
    },
    enabled: !!runId,
  });
}

export function useErrorMining(runId: number | null) {
  return useQuery({
    queryKey: ["error-mining", runId],
    queryFn: async () => {
      const { data } = await api.get(`/training-runs/${runId}/errors`);
      return data as { errors: import("@/types").ErrorMiningEntry[]; total_evaluated: number };
    },
    enabled: !!runId,
  });
}

export function useCompareRuns(runIdA: number | null, runIdB: number | null) {
  return useQuery({
    queryKey: ["compare-runs", runIdA, runIdB],
    queryFn: async () => {
      const { data } = await api.get(`/training-runs/${runIdA}/compare/${runIdB}`);
      return data;
    },
    enabled: !!runIdA && !!runIdB,
  });
}

export function useActivateModel(runId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async () => {
      const { data } = await api.post(`/training-runs/${runId}/activate`);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["training-runs"] });
    },
  });
}
