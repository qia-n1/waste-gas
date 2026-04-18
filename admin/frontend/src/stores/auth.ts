import { computed, ref } from "vue";
import { defineStore } from "pinia";

import client from "@/api/client";

interface AuthUser {
  username: string;
  role: string;
  name: string;
}

export const useAuthStore = defineStore("auth", () => {
  const token = ref(localStorage.getItem("admin-token") ?? "");
  const user = ref<AuthUser | null>(
    localStorage.getItem("admin-user")
      ? (JSON.parse(localStorage.getItem("admin-user") as string) as AuthUser)
      : null,
  );
  const loading = ref(false);

  const isAuthenticated = computed(() => Boolean(token.value));

  const setSession = (nextToken: string, nextUser: AuthUser) => {
    token.value = nextToken;
    user.value = nextUser;
    localStorage.setItem("admin-token", nextToken);
    localStorage.setItem("admin-user", JSON.stringify(nextUser));
  };

  const clearSession = () => {
    token.value = "";
    user.value = null;
    localStorage.removeItem("admin-token");
    localStorage.removeItem("admin-user");
  };

  const login = async (username: string, password: string) => {
    loading.value = true;
    try {
      const { data } = await client.post("/auth/login", { username, password });
      setSession(data.access_token, data.user as AuthUser);
      return data.user as AuthUser;
    } finally {
      loading.value = false;
    }
  };

  const logout = () => {
    clearSession();
  };

  return { token, user, loading, isAuthenticated, login, logout, setSession, clearSession };
});
