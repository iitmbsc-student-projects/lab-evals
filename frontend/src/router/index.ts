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
  // Admin
  {
    path: '/admin',
    component: () => import('../components/layout/AdminLayout.vue'),
    meta: { role: 'admin' },
    children: [
      { path: 'subjects', component: () => import('../views/admin/SubjectsView.vue') },
      { path: 'questions', component: () => import('../views/admin/QuestionsView.vue') },
      { path: 'users', component: () => import('../views/admin/UsersView.vue') },
      { path: 'enrollments', component: () => import('../views/admin/EnrollmentsView.vue') },
      { path: 'evaluations', component: () => import('../views/admin/EvaluationsView.vue') },
      { path: 'audit', component: () => import('../views/admin/AuditView.vue') },
    ],
  },
  // TA
  {
    path: '/ta',
    component: () => import('../components/layout/TALayout.vue'),
    meta: { role: 'ta' },
    children: [
      { path: 'profile', component: () => import('../views/ta/ProfileView.vue') },
      { path: 'students', component: () => import('../views/ta/StudentsView.vue') },
      { path: 'subjects', component: () => import('../views/ta/SubjectsView.vue') },
      { path: 'questions', component: () => import('../views/ta/QuestionsView.vue') },
      { path: 'evaluations', component: () => import('../views/ta/EvaluationsView.vue') },
    ],
  },
  // Student
  {
    path: '/student',
    component: () => import('../components/layout/StudentLayout.vue'),
    meta: { role: 'student' },
    children: [
      { path: 'profile', component: () => import('../views/student/ProfileView.vue') },
      { path: 'questions', component: () => import('../views/student/QuestionsView.vue') },
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
router.beforeEach((to, from, next) => {
  const auth = useAuthStore()
  if (to.meta.public) return next()
  if (!auth.token || !auth.role) return next('/login')
  if (to.meta.role && to.meta.role !== auth.role) return next('/login')
  next()
})

export default router
