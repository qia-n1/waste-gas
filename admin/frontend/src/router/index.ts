import { createRouter, createWebHistory } from "vue-router";

import AdminDashboard from "@/views/AdminDashboard.vue";
import LoginView from "@/views/Login.vue";
import UserManagementView from "@/views/UserManagement.vue";

const router = createRouter({
  history: createWebHistory(),
  routes: [
    { path: "/login", name: "login", component: LoginView },
    { path: "/", name: "dashboard", component: AdminDashboard },
    { path: "/users", name: "users", component: UserManagementView },
  ],
});

router.beforeEach((to) => {
  const token = localStorage.getItem("admin-token");
  if (!token && to.name !== "login") {
    return { name: "login" };
  }
  if (token && to.name === "login") {
    return { name: "dashboard" };
  }
  return true;
});

export default router;
