import { useMutation, useQuery, useQueryClient } from "@tanstack/react-query";
import api from "./client";
import { useAuthStore, type AuthUser } from "@/stores/authStore";

interface LoginResponse {
  access_token: string;
  user: AuthUser;
}

export function useLogin() {
  const setAuth = useAuthStore((s) => s.setAuth);
  return useMutation({
    mutationFn: async (body: { username: string; password: string }) => {
      const { data } = await api.post<LoginResponse>("/auth/login", body);
      return data;
    },
    onSuccess: (data) => {
      setAuth(data.access_token, data.user);
    },
  });
}

export function useLogout() {
  const logout = useAuthStore((s) => s.logout);
  const queryClient = useQueryClient();
  return () => {
    logout();
    queryClient.clear();
  };
}

export function useMe() {
  return useQuery<AuthUser>({
    queryKey: ["auth-me"],
    queryFn: async () => {
      const { data } = await api.get("/auth/me");
      return data;
    },
    enabled: !!useAuthStore.getState().token,
    retry: false,
  });
}

export function useChangePassword() {
  return useMutation({
    mutationFn: async (body: { current_password: string; new_password: string }) => {
      const { data } = await api.patch("/auth/me/password", body);
      return data;
    },
  });
}
