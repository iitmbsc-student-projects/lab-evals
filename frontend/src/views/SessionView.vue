<!--
  SessionView.vue
  Loads the session for the current user and renders TA or Student panel accordingly.
-->
<template>
  <div>
    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-16">
      <AppSpinner size="lg" text="Loading session..." centered />
    </div>

    <!-- Not found / not authorized -->
    <div
      v-else-if="!session"
      class="text-center py-16 bg-white rounded-xl border border-zinc-200 shadow-sm"
    >
      <p class="text-zinc-700 font-medium mb-4">Not authorized or session not found.</p>
      <RouterLink to="/" class="text-sm text-zinc-500 underline hover:text-zinc-800">
        Back to Home
      </RouterLink>
    </div>

    <!-- TA Panel -->
    <TASessionPanel v-else-if="session.role === 'ta'" :session="session" />

    <!-- Student Panel -->
    <StudentSessionPanel v-else :session="session" />
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getMySessions } from '../api/auth'
import type { MySession } from '../types/api'
import AppSpinner from '../components/common/AppSpinner.vue'
import TASessionPanel from '../components/session/TASessionPanel.vue'
import StudentSessionPanel from '../components/session/StudentSessionPanel.vue'

const route = useRoute()
const session = ref<MySession | null>(null)
const loading = ref(true)

onMounted(async () => {
  const sessionId = Number(route.params.sessionId)
  try {
    const sessions = await getMySessions()
    session.value = sessions.find((s) => s.lab_session_id === sessionId) ?? null
  } finally {
    loading.value = false
  }
})
</script>
