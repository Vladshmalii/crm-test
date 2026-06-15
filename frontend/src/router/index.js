import { createRouter, createWebHistory } from 'vue-router'
import Login from '../views/Login.vue'
import ChatterDashboard from '../views/ChatterDashboard.vue'
import TeamleadDashboard from '../views/TeamleadDashboard.vue'
import { useAuthStore } from '../stores/auth'

const router = createRouter({
  history: createWebHistory(),
  routes: [
    {
      path: '/login',
      name: 'login',
      component: Login
    },
    {
      path: '/',
      name: 'chatter',
      component: ChatterDashboard,
      meta: { requiresAuth: true, role: 'chatter' }
    },
    {
      path: '/teamlead',
      name: 'teamlead',
      component: TeamleadDashboard,
      meta: { requiresAuth: true, role: 'teamlead' }
    }
  ]
})

router.beforeEach((to, from, next) => {
  const authStore = useAuthStore()
  if (to.meta.requiresAuth && !authStore.token) {
    next('/login')
  } else if (to.path === '/login' && authStore.token) {
    next(authStore.role === 'teamlead' ? '/teamlead' : '/')
  } else {
    next()
  }
})

export default router
