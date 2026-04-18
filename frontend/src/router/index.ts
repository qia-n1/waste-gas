import { createRouter, createWebHistory } from 'vue-router';

const routes = [
  {
    path: '/',
    redirect: '/login'
  },
  {
    path: '/twin',
    name: 'Twin',
    component: () => import('@/components/FactoryScene.vue')
  },
  {
    path: '/login',
    name: 'Login',
    component: () => import('@/views/Login.vue')
  },
  {
    path: '/dashboard',
    name: 'Dashboard',
    component: () => import('@/views/Dashboard.vue')
  },
  {
    path: '/alerts',
    name: 'Alerts',
    component: () => import('@/views/Alerts.vue')
  },
  {
    path: '/alerts/:id',
    name: 'AlertDetails',
    component: () => import('@/views/AlertDetails.vue')
  }
];

const router = createRouter({
  history: createWebHistory(),
  routes
});

export default router;