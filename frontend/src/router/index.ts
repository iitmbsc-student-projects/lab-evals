import { createRouter, createWebHistory } from 'vue-router'

import LoginView from '../views/LoginView.vue'
import { useAuthStore } from '../store/auth'

const routes = [
  {
    path: '/login',
    name: 'login',
    component: LoginView,
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('../views/PortalView.vue'),
    meta: { requiresAuth: true },
  },
  {
    path: '/sessions/:sessionId',
    component: () => import('../views/SessionView.vue'),
    meta: { requiresAuth: true },
  },
  // Admin
  {
    path: '/admin',
    component: () => import('../components/layout/AdminLayout.vue'),
    meta: { admin: true },
    children: [
      { path: 'subjects', component: () => import('../views/admin/SubjectsView.vue') },
      { path: 'questions', component: () => import('../views/admin/QuestionsView.vue') },
      { path: 'users', component: () => import('../views/admin/UsersView.vue') },
      { path: 'lab-sessions', component: () => import('../views/admin/LabSessionsView.vue') },
      {
        path: 'session-assignments',
        component: () => import('../views/admin/SessionAssignmentsView.vue'),
      },
      { path: 'evaluations', component: () => import('../views/admin/EvaluationsView.vue') },
      { path: 'audit', component: () => import('../views/admin/AuditView.vue') },
    ],
  },
  // Default redirect
  { path: '/:pathMatch(.*)*', redirect: '/login' },
]

const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes,
})

// RBAC navigation guard
router.beforeEach((to, _from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (!auth.token) return next('/login')
  if (to.meta.admin && !auth.is_admin) return next('/')
  next()
})

export default router
