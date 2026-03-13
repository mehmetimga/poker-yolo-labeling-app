import { useQuery, useMutation, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import type { AuthUser } from "@/stores/authStore";

export function useUsers() {
  return useQuery<AuthUser[]>({
    queryKey: ["users"],
    queryFn: async () => {
      const { data } = await api.get("/users");
      return data;
    },
  });
}

export function useCreateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async (body: {
      username: string;
      email: string;
      password: string;
      role: string;
    }) => {
      const { data } = await api.post("/users", body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}

export function useUpdateUser() {
  const queryClient = useQueryClient();
  return useMutation({
    mutationFn: async ({
      id,
      ...body
    }: {
      id: number;
      role?: string;
      is_active?: boolean;
    }) => {
      const { data } = await api.patch(`/users/${id}`, body);
      return data;
    },
    onSuccess: () => {
      queryClient.invalidateQueries({ queryKey: ["users"] });
    },
  });
}
