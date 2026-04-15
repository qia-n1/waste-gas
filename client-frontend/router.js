import { createRouter, createWebHashHistory } from 'vue-router'

import AuthPage from './pages/auth/login.vue'
import IndexPage from './pages/index/index.vue'
import MonitorRealtimePage from './pages/monitor/realtime.vue'
import AlertsListPage from './pages/alerts/list.vue'
import AlertsDetailPage from './pages/alerts/detail.vue'
import ProfilePage from './pages/profile/index.vue'
import SettingsPage from './pages/settings/index.vue'

const routes = [
  { path: '/', redirect: '/auth/login' },
  { path: '/auth/login', component: AuthPage },
  { path: '/pages/index/index', component: IndexPage },
  { path: '/pages/monitor/realtime', component: MonitorRealtimePage },
  { path: '/pages/alerts/list', component: AlertsListPage },
  { path: '/pages/alerts/detail', component: AlertsDetailPage },
  { path: '/pages/profile/index', component: ProfilePage },
  { path: '/pages/settings/index', component: SettingsPage },
]

const router = createRouter({
  history: createWebHashHistory(),
  routes,
})

router.beforeEach((to) => {
  const token = localStorage.getItem('authToken')
  const isAuthRoute = to.path === '/auth/login'

  if (!token && !isAuthRoute) {
    return '/auth/login'
  }

  if (token && isAuthRoute) {
    return '/pages/index/index'
  }

  return true
})

export default router
