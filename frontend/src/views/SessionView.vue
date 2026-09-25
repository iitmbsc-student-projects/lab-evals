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

      <!-- Access may have changed under us; never destroy the panel (and the
           TA's half-entered marks) over a background refresh — say so instead. -->
      <template v-else>
        <div
          v-if="accessWarning"
          class="mb-6 bg-amber-50 border border-amber-300 rounded-lg px-4 py-3 text-amber-800 text-sm font-medium"
        >
          You may no longer have access to this session — reload to confirm.
        </div>

        <!-- TA Panel -->
        <TASessionPanel v-if="session.role === 'ta'" :session="session" />

        <!-- Student Panel -->
        <StudentSessionPanel v-else :session="session" />
      </template>
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
import { usePolling, type PollContext } from '../composables/usePolling'

const route = useRoute()
const session = ref<MySession | null>(null)
const accessWarning = ref(false)

// `ctx` is present only on a poll tick: it carries the abort signal and the
// staleness check that keeps a late tick from overwriting fresher state.
async function loadSession(ctx?: PollContext) {
  const sessionId = Number(route.params.sessionId)
  const sessions = await getMySessions(ctx?.signal)
  if (ctx?.isStale()) return
  const found = sessions.find((s) => s.lab_session_id === sessionId) ?? null
  if (found) {
    session.value = found
    accessWarning.value = false
    return
  }
  // A poll tick must never downgrade a loaded session to null: an admin
  // fixing a roster typo (remove + re-add) would otherwise unmount the panel
  // and take the TA's unsaved form with it. Keep the last known session and
  // warn non-destructively; only the initial load shows "not found".
  if (ctx) accessWarning.value = session.value !== null
  else session.value = null
}

const {
  loading,
  error,
  run: load,
} = useAsyncTask(() => loadSession(), { immediate: true })

// Keeps `accepting_evaluations` (and the role) current, so the panel below
// enables or disables its controls without a reload. No staleness indicator
// here: the panel underneath polls on the same cadence and shows its own.
//
// Polls the raw loader, not the task's refresh(): a failed background tick is
// swallowed by usePolling instead of painting an error over a live panel.
usePolling(loadSession)
</script>
