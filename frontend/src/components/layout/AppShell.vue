<!--
  AppShell.vue
  Neutral app shell layout for authenticated non-admin users.
  Header: app title, user info, Home link, Admin link (admin only), Logout.
-->
<template>
  <div class="min-h-screen bg-zinc-50">
    <header
      class="bg-gradient-to-r from-zinc-800 to-zinc-700 text-white px-4 sm:px-6 py-3 sm:py-4 shadow-md"
    >
      <div class="max-w-7xl mx-auto flex items-center justify-between gap-3">
        <div class="min-w-0">
          <h1 class="text-lg sm:text-2xl font-bold truncate">Lab Evaluation</h1>
        </div>
        <div class="flex items-center gap-2 sm:gap-4 shrink-0">
          <RouterLink
            to="/"
            class="px-3 py-1.5 rounded-md text-sm font-medium text-zinc-200 hover:text-white hover:bg-zinc-600 transition-colors"
          >
            Home
          </RouterLink>
          <RouterLink
            v-if="auth.is_admin"
            to="/admin/subjects"
            class="px-3 py-1.5 rounded-md text-sm font-medium text-zinc-200 hover:text-white hover:bg-zinc-600 transition-colors"
          >
            Admin
          </RouterLink>
          <div class="text-right hidden sm:block min-w-0 max-w-[40vw]">
            <p class="text-sm font-medium truncate">{{ auth.user?.name }}</p>
            <p class="text-xs text-zinc-300 truncate">{{ auth.user?.email }}</p>
          </div>
          <button
            @click="handleLogout"
            class="px-3 sm:px-4 py-2 bg-zinc-600 hover:bg-zinc-500 rounded-md text-sm font-medium transition-colors shrink-0"
          >
            Logout
          </button>
        </div>
      </div>
    </header>
    <main class="p-6 max-w-7xl mx-auto">
      <RouterView />
    </main>
  </div>
</template>

<script setup lang="ts">
import { useRouter } from 'vue-router'
import { useAuthStore } from '../../store/auth'

const auth = useAuthStore()
const router = useRouter()

function handleLogout() {
  auth.clearAuth()
  router.push('/login')
}
</script>
