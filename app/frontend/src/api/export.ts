import { useMutation } from "@tanstack/react-query";
import api from "./client";

export function useExportYolo(projectId: number) {
  return useMutation({
    mutationFn: async (outputDir?: string) => {
      const params = outputDir ? { output_dir: outputDir } : {};
      const { data } = await api.post(
        `/projects/${projectId}/export/yolo`,
        null,
        { params }
      );
      return data;
    },
  });
}

export function useExportMetadata(projectId: number) {
  return useMutation({
    mutationFn: async (outputDir?: string) => {
      const params = outputDir ? { output_dir: outputDir } : {};
      const { data } = await api.post(
        `/projects/${projectId}/export/metadata`,
        null,
        { params }
      );
      return data;
    },
  });
}
