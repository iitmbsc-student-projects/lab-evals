<!--
  PortalView.vue
  Main portal: shows all sessions the current user is enrolled in (as student or TA).
-->
<template>
  <div>
    <h2 class="text-2xl font-bold text-zinc-900 mb-6">My Sessions</h2>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <AppSpinner size="lg" text="Loading sessions..." centered />
    </div>

    <!-- Empty state -->
    <div
      v-else-if="sessions.length === 0"
      class="text-center py-16 bg-white rounded-xl border border-zinc-200 shadow-sm"
    >
      <svg
        class="mx-auto h-12 w-12 text-zinc-400 mb-4"
        fill="none"
        viewBox="0 0 24 24"
        stroke="currentColor"
      >
        <path
          stroke-linecap="round"
          stroke-linejoin="round"
          stroke-width="2"
          d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
        />
      </svg>
      <p class="text-zinc-500 text-sm">You have no sessions assigned.</p>
    </div>

    <!-- Session grid -->
    <div v-else class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
      <div
        v-for="session in sessions"
        :key="session.lab_session_id"
        class="bg-white rounded-xl border border-zinc-200 shadow-sm hover:shadow-md transition-shadow cursor-pointer p-5 flex flex-col gap-3"
        @click="router.push(`/sessions/${session.lab_session_id}`)"
      >
        <div>
          <h3 class="text-base font-bold text-zinc-900 truncate">{{ session.subject_name }}</h3>
          <p class="text-sm text-zinc-500 mt-0.5">{{ formatDate(session.date) }}</p>
        </div>
        <div class="flex items-center gap-2 flex-wrap">
          <AppBadge :variant="session.role === 'ta' ? 'info' : 'success'">
            {{ session.role === 'ta' ? 'TA' : 'Student' }}
          </AppBadge>
          <AppBadge :variant="session.accepting_evaluations ? 'success' : 'warning'">
            {{ session.accepting_evaluations ? 'Open' : 'Closed' }}
          </AppBadge>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { getMySessions } from '../api/auth'
import type { MySession } from '../types/api'
import AppSpinner from '../components/common/AppSpinner.vue'
import AppBadge from '../components/common/AppBadge.vue'
import { formatDate } from '@/utils/date'

const router = useRouter()
const sessions = ref<MySession[]>([])
const loading = ref(true)

onMounted(async () => {
  try {
    sessions.value = await getMySessions()
  } finally {
    loading.value = false
  }
})
</script>
