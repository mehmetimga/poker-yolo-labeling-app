import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type { Annotation, SchemaScoreResponse, Taxonomy } from "@/types";

export function useTaxonomy() {
  return useQuery<Taxonomy>({
    queryKey: ["taxonomy"],
    queryFn: async () => {
      const { data } = await api.get("/schemas/taxonomy");
      return data;
    },
    staleTime: Infinity,
  });
}

export function useSchemaDefinitions() {
  return useQuery({
    queryKey: ["schema-definitions"],
    queryFn: async () => {
      const { data } = await api.get("/schemas");
      return data;
    },
    staleTime: Infinity,
  });
}

export function useScoreSchemas() {
  return useMutation({
    mutationFn: async (imageId: number): Promise<SchemaScoreResponse> => {
      const { data } = await api.post("/schemas/score", {
        image_id: imageId,
      });
      return data;
    },
  });
}

export function useAssignSchema(imageId: number) {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (schemaName: string) => {
      const { data } = await api.put(`/schemas/images/${imageId}/schema`, {
        schema_name: schemaName,
      });
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["image", imageId] });
      queryClient.invalidateQueries({ queryKey: ["images"] });
    },
  });
}

export function useSchemaTemplate() {
  return useMutation({
    mutationFn: async (schemaName: string): Promise<Annotation[]> => {
      const { data } = await api.get(`/schemas/templates/${schemaName}`);
      return data;
    },
  });
}
