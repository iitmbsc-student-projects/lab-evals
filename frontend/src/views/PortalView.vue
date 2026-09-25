<!--
  PortalView.vue
  Main portal: shows all sessions the current user is enrolled in (as student or TA).
-->
<template>
  <div>
    <div class="flex items-baseline justify-between gap-4 mb-6">
      <h2 class="text-2xl font-bold text-zinc-900">My Sessions</h2>
      <AppPollStatus :text="pollStatus" />
    </div>

    <AppAsyncSection
      :loading="loading"
      :error="error"
      :empty="sessions.length === 0"
      :has-content="sessions.length > 0"
      loading-text="Loading sessions..."
      spacing="lg"
      @retry="load()"
    >
      <!-- Empty state -->
      <template #empty>
        <svg
          class="mx-auto h-12 w-12 text-zinc-400 mb-4"
          fill="none"
          viewBox="0 0 24 24"
          stroke="currentColor"
          aria-hidden="true"
        >
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M9 5H7a2 2 0 00-2 2v12a2 2 0 002 2h10a2 2 0 002-2V7a2 2 0 00-2-2h-2M9 5a2 2 0 002 2h2a2 2 0 002-2M9 5a2 2 0 012-2h2a2 2 0 012 2"
          />
        </svg>
        <p class="text-zinc-500 text-sm">You have no sessions assigned.</p>
      </template>

      <!-- Session grid -->
      <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-3 gap-4">
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
    </AppAsyncSection>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { getMySessions } from '../api/auth'
import type { MySession } from '../types/api'
import AppAsyncSection from '../components/common/AppAsyncSection.vue'
import AppBadge from '../components/common/AppBadge.vue'
import AppPollStatus from '../components/common/AppPollStatus.vue'
import { useAsyncTask } from '../composables/useAsync'
import { usePolling, type PollContext } from '../composables/usePolling'
import { formatDate } from '@/utils/date'

const router = useRouter()
const sessions = ref<MySession[]>([])

// `ctx` is present only on a poll tick: it carries the abort signal and the
// staleness check that keeps a late tick from overwriting fresher state.
async function loadSessions(ctx?: PollContext) {
  const data = await getMySessions(ctx?.signal)
  if (ctx?.isStale()) return
  sessions.value = data
}

const {
  loading,
  error,
  run: load,
} = useAsyncTask(() => loadSessions(), { immediate: true })

// Sessions open and close while this list is on screen; nothing here is
// editable, so a background refresh is always safe.
//
// The poll drives the raw loader rather than the task's refresh(): usePolling
// swallows a failed tick, whereas useAsyncTask would publish it into `error`
// and paint a banner over data that is still good.
const { statusText: pollStatus } = usePolling(loadSessions)
</script>
