<!--
  StudentLayout.vue
  Layout for student dashboard. Restricts to student role.
-->
<template>
  <div class="min-h-screen bg-zinc-50">
    <header
      class="bg-gradient-to-r from-blue-600 to-blue-500 text-white px-4 sm:px-6 py-3 sm:py-4 shadow-md"
    >
      <div class="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="text-lg sm:text-2xl font-bold truncate">Lab Evaluation</h1>
          <p class="text-xs sm:text-sm text-blue-100 mt-0.5">Student Portal</p>
        </div>
        <div class="flex items-center gap-2 sm:gap-4 shrink-0">
          <div class="text-right hidden sm:block min-w-0 max-w-[40vw]">
            <p class="text-sm font-medium truncate">{{ user?.name }}</p>
            <p class="text-xs text-blue-100 truncate">{{ user?.email }}</p>
          </div>
          <button
            @click="handleLogout"
            class="px-3 sm:px-4 py-2 bg-blue-700 hover:bg-blue-800 rounded-md text-sm font-medium transition-colors shrink-0"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
    <nav class="bg-white border-b border-zinc-200 shadow-sm">
      <div class="max-w-7xl mx-auto flex gap-1 overflow-x-auto no-scrollbar px-4 sm:px-6 py-3">
        <RouterLink
          to="/student/questions"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap shrink-0"
          active-class="bg-blue-600 text-white"
          :class="$route.path === '/student/questions' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Questions
        </RouterLink>
        <RouterLink
          to="/student/profile"
          class="px-4 py-2 rounded-md text-sm font-medium transition-colors whitespace-nowrap shrink-0"
          active-class="bg-blue-600 text-white"
          :class="$route.path === '/student/profile' ? '' : 'text-zinc-700 hover:bg-zinc-100'"
        >
          Profile
        </RouterLink>
      </div>
    </nav>
    <main class="p-6 max-w-7xl mx-auto">
      <RouterView />
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
