<!--
  SessionView.vue
  Loads the session for the current user and renders TA or Student panel accordingly.
-->
<template>
  <div>
    <!--
      has-content is always true here: the fallback card below carries the
      Back to Home link, so the error banner renders above it instead of
      replacing it and leaving a dead page with no navigation.
    -->
    <AppAsyncSection
      :loading="loading"
      :error="error"
      :has-content="true"
      loading-text="Loading session..."
      spacing="lg"
      @retry="load()"
    >
      <!-- Not found / not authorized / failed to load -->
      <div
        v-if="!session"
        class="text-center py-16 bg-white rounded-xl border border-zinc-200 shadow-sm"
      >
        <p v-if="!error" class="text-zinc-700 font-medium mb-4">
          Not authorized or session not found.
        </p>
        <RouterLink to="/" class="text-sm text-zinc-500 underline hover:text-zinc-800">
          Back to Home
        </RouterLink>
      </div>

      <!-- TA Panel -->
      <TASessionPanel v-else-if="session.role === 'ta'" :session="session" />

      <!-- Student Panel -->
      <StudentSessionPanel v-else :session="session" />
    </AppAsyncSection>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRoute } from 'vue-router'
import { getMySessions } from '../api/auth'
import type { MySession } from '../types/api'
import AppAsyncSection from '../components/common/AppAsyncSection.vue'
import TASessionPanel from '../components/session/TASessionPanel.vue'
import StudentSessionPanel from '../components/session/StudentSessionPanel.vue'
import { useAsyncTask } from '../composables/useAsync'

const route = useRoute()
const session = ref<MySession | null>(null)

const {
  loading,
  error,
  run: load,
} = useAsyncTask(
  async () => {
    const sessionId = Number(route.params.sessionId)
    const sessions = await getMySessions()
    session.value = sessions.find((s) => s.lab_session_id === sessionId) ?? null
  },
  { immediate: true },
)
</script>
