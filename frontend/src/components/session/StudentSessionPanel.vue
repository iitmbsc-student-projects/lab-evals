<!--
  StudentSessionPanel.vue
  Read-only panel for students: shows questions and whether each has been evaluated.
  Never shows marking or remarks.
-->
<template>
  <div class="space-y-6">
    <!-- Session header -->
    <div class="flex items-start justify-between gap-4">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">{{ session.subject_name }}</h2>
        <p class="text-sm text-zinc-500 mt-0.5">{{ formatDate(session.date) }}</p>
      </div>
      <AppPollStatus :text="pollStatus" class="mt-1" />
    </div>

    <!-- Closed banner -->
    <div
      v-if="!session.accepting_evaluations"
      class="bg-amber-50 border border-amber-300 rounded-lg px-4 py-3 text-amber-800 text-sm font-medium"
    >
      This session is not currently accepting evaluations.
    </div>

    <AppAsyncSection
      :loading="loading"
      :error="error"
      :has-content="questions.length > 0"
      loading-text="Loading questions..."
      @retry="load()"
    >
      <!-- Questions table -->
      <div class="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-zinc-100">
          <h3 class="text-base font-semibold text-zinc-900">Questions</h3>
        </div>
        <AppTable :isEmpty="questions.length === 0" emptyMessage="No questions for this session.">
          <template #head>
            <th>#</th>
            <th>Question</th>
            <th>Status</th>
          </template>
          <tr v-for="(q, idx) in questions" :key="q.id">
            <td class="text-zinc-500">{{ idx + 1 }}</td>
            <td>{{ q.text }}</td>
            <td>
              <AppBadge :variant="isEvaluated(q.id) ? 'success' : 'warning'">
                {{ isEvaluated(q.id) ? 'Evaluated' : 'Pending' }}
              </AppBadge>
            </td>
          </tr>
        </AppTable>
      </div>
    </AppAsyncSection>
  </div>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import type { MySession, QuestionResponse, StudentEvaluationResponse } from '../../types/api'
import { getQuestions, getEvaluations } from '../../api/student'
import AppAsyncSection from '../common/AppAsyncSection.vue'
import AppTable from '../common/AppTable.vue'
import AppBadge from '../common/AppBadge.vue'
import AppPollStatus from '../common/AppPollStatus.vue'
import { useAsyncTask } from '../../composables/useAsync'
import { usePolling, type PollContext } from '../../composables/usePolling'
import { formatDate } from '@/utils/date'

const props = defineProps<{ session: MySession }>()

const questions = ref<QuestionResponse[]>([])
const evaluations = ref<StudentEvaluationResponse[]>([])

function isEvaluated(questionId: number): boolean {
  return evaluations.value.some((e) => e.question_id === questionId)
}

// The question set for a session does not change while the page is open, so
// it is fetched once on mount (and again after an error) rather than polled.
async function loadQuestions() {
  questions.value = await getQuestions(props.session.lab_session_id)
}

// The live half: which questions have been graded yet. This is the poll
// target — one request per tick.
async function loadEvaluations(ctx?: PollContext) {
  const data = await getEvaluations(props.session.lab_session_id, ctx?.signal)
  if (ctx?.isStale()) return
  evaluations.value = data
}

const {
  loading,
  error,
  run: load,
} = useAsyncTask(
  async () => {
    await Promise.all([loadQuestions(), loadEvaluations()])
  },
  { immediate: true },
)

// A student watches this table for their evaluations to land; the panel is
// read-only, so nothing can be lost to a background refresh.
//
// Polls the raw loader rather than the task's refresh(): usePolling swallows a
// failed tick, where useAsyncTask would surface it as a banner over good data.
const { statusText: pollStatus } = usePolling(loadEvaluations)
</script>
