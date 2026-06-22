<!--
  StudentSessionPanel.vue
  Read-only panel for students: shows questions and whether each has been evaluated.
  Never shows marking or remarks.
-->
<template>
  <div class="space-y-6">
    <!-- Session header -->
    <div>
      <h2 class="text-2xl font-bold text-zinc-900">{{ session.subject_name }}</h2>
      <p class="text-sm text-zinc-500 mt-0.5">{{ formatDate(session.date) }}</p>
    </div>

    <!-- Closed banner -->
    <div
      v-if="!session.accepting_evaluations"
      class="bg-amber-50 border border-amber-300 rounded-lg px-4 py-3 text-amber-800 text-sm font-medium"
    >
      This session is not currently accepting evaluations.
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" text="Loading..." centered />
    </div>

    <!-- Questions table -->
    <div v-else class="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
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
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import type { MySession, QuestionResponse, StudentEvaluationResponse } from '../../types/api'
import { getQuestions, getEvaluations } from '../../api/student'
import AppSpinner from '../common/AppSpinner.vue'
import AppTable from '../common/AppTable.vue'
import AppBadge from '../common/AppBadge.vue'
import { formatDate } from '@/utils/date'

const props = defineProps<{ session: MySession }>()

const loading = ref(true)
const questions = ref<QuestionResponse[]>([])
const evaluations = ref<StudentEvaluationResponse[]>([])

function isEvaluated(questionId: number): boolean {
  return evaluations.value.some((e) => e.question_id === questionId)
}

onMounted(async () => {
  try {
    const [q, e] = await Promise.all([
      getQuestions(props.session.lab_session_id),
      getEvaluations(props.session.lab_session_id),
    ])
    questions.value = q
    evaluations.value = e
  } finally {
    loading.value = false
  }
})
</script>
