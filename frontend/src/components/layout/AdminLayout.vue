<!--
  AdminLayout.vue
  Layout for admin dashboard. Restricts to admin role.
-->
<template>
  <div class="min-h-screen bg-zinc-50">
    <header class="bg-gradient-to-r from-zinc-800 to-zinc-700 text-white px-6 py-4 shadow-md">
      <div class="max-w-7xl mx-auto flex items-center justify-between">
        <div>
          <h1 class="text-2xl font-bold">Lab Evaluation</h1>
          <p class="text-sm text-zinc-300 mt-0.5">Admin Portal</p>
        </div>
        <div class="flex items-center gap-4">
          <div class="text-right">
            <p class="text-sm font-medium">{{ user?.name }}</p>
            <p class="text-xs text-zinc-300">{{ user?.email }}</p>
          </div>
          <button
            @click="handleLogout"
            class="px-4 py-2 bg-zinc-600 hover:bg-zinc-500 rounded-md text-sm font-medium transition-colors"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
    <nav class="bg-white border-b border-zinc-200 px-6 py-3 shadow-sm">
      <div class="max-w-7xl mx-auto flex gap-1">
        <RouterLink
          to="/admin/subjects"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
          active-class="bg-zinc-800 text-white"
          :class="$route.path === '/admin/subjects' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Subjects
        </RouterLink>
        <RouterLink
          to="/admin/questions"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
          active-class="bg-zinc-800 text-white"
          :class="$route.path === '/admin/questions' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Questions
        </RouterLink>
        <RouterLink
          to="/admin/users"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
          active-class="bg-zinc-800 text-white"
          :class="$route.path === '/admin/users' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Users
        </RouterLink>
        <RouterLink
          to="/admin/enrollments"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
          active-class="bg-zinc-800 text-white"
          :class="$route.path === '/admin/enrollments' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Enrollments
        </RouterLink>
        <RouterLink
          to="/admin/evaluations"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
          active-class="bg-zinc-800 text-white"
          :class="$route.path === '/admin/evaluations' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Evaluations
        </RouterLink>
        <RouterLink
          to="/admin/audit"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors"
          active-class="bg-zinc-800 text-white"
          :class="$route.path === '/admin/audit' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Audit
        </RouterLink>
      </div>
    </nav>
    <main class="p-6 max-w-7xl mx-auto">
      <router-view />
    </main>
  </div>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'

const auth = useAuthStore()
const router = useRouter()

const user = computed(() => auth.user)

function handleLogout() {
  auth.clearAuth()
  router.push('/login')
}
</script>
