<!--
  TASessionPanel.vue
  Panel for TAs to view and manage evaluations within a session.
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
      This session is not accepting evaluations. All create, edit, and delete operations are
      disabled.
    </div>

    <!-- Loading -->
    <div v-if="loading" class="flex justify-center py-12">
      <AppSpinner size="lg" text="Loading data..." centered />
    </div>

    <template v-else>
      <!-- Create evaluation form -->
      <div class="bg-white rounded-xl border border-zinc-200 shadow-sm p-6">
        <h3 class="text-base font-semibold text-zinc-900 mb-4">Add Evaluation</h3>
        <form @submit.prevent="handleCreate" class="space-y-4">
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <AppCombobox
              v-model="form.student_id"
              label="Student"
              placeholder="Search student..."
              :options="studentOptions"
              required
              :disabled="!session.accepting_evaluations"
            />
            <AppSelect
              v-model="form.question_id"
              label="Question"
              required
              :disabled="!session.accepting_evaluations || form.student_id === null"
            >
              <option value="">Select question...</option>
              <option
                v-for="q in availableQuestions"
                :key="q.id"
                :value="q.id"
              >
                {{ q.text }}
              </option>
            </AppSelect>
          </div>
          <div class="grid grid-cols-1 sm:grid-cols-2 gap-4">
            <AppSelect
              v-model="form.marking"
              label="Marking (1–5)"
              required
              :disabled="!session.accepting_evaluations"
            >
              <option value="">Select mark...</option>
              <option v-for="m in [1, 2, 3, 4, 5]" :key="m" :value="m">{{ m }}</option>
            </AppSelect>
            <AppInput
              v-model="form.remarks"
              label="Remarks (optional)"
              placeholder="Optional remarks..."
              :disabled="!session.accepting_evaluations"
            />
          </div>
          <div class="flex items-center gap-3">
            <AppButton
              type="submit"
              :disabled="!session.accepting_evaluations || !canSubmit || creating"
            >
              {{ creating ? 'Adding...' : 'Add Evaluation' }}
            </AppButton>
            <p v-if="createError" class="text-sm text-red-600">{{ createError }}</p>
          </div>
        </form>
      </div>

      <!-- Evaluations table -->
      <div class="bg-white rounded-xl border border-zinc-200 shadow-sm overflow-hidden">
        <div class="px-6 py-4 border-b border-zinc-100">
          <h3 class="text-base font-semibold text-zinc-900">My Evaluations</h3>
        </div>
        <AppTable :isEmpty="evaluations.length === 0" emptyMessage="No evaluations yet.">
          <template #head>
            <th>Student</th>
            <th>Question</th>
            <th>Marking</th>
            <th>Remarks</th>
            <th>Actions</th>
          </template>
          <tr v-for="ev in evaluations" :key="ev.id">
            <td>{{ studentName(ev.student_id) }}</td>
            <td class="max-w-xs truncate">{{ questionText(ev.question_id) }}</td>
            <td>
              <AppBadge variant="info">{{ ev.marking }}/5</AppBadge>
            </td>
            <td class="max-w-xs truncate text-zinc-500">{{ ev.remarks || '—' }}</td>
            <td>
              <div class="flex items-center gap-2">
                <!-- Edit inline -->
                <template v-if="editingId === ev.id">
                  <AppSelect
                    v-model="editForm.marking"
                    :disabled="!session.accepting_evaluations"
                    class="w-20"
                  >
                    <option v-for="m in [1, 2, 3, 4, 5]" :key="m" :value="m">{{ m }}</option>
                  </AppSelect>
                  <AppInput
                    v-model="editForm.remarks"
                    placeholder="Remarks"
                    :disabled="!session.accepting_evaluations"
                    class="w-32"
                  />
                  <AppButton
                    size="sm"
                    variant="success"
                    :disabled="!session.accepting_evaluations || saving"
                    @click="handleUpdate(ev.id)"
                  >
                    Save
                  </AppButton>
                  <AppButton size="sm" variant="ghost" @click="cancelEdit">Cancel</AppButton>
                </template>
                <template v-else>
                  <AppButton
                    size="sm"
                    variant="secondary"
                    :disabled="!session.accepting_evaluations"
                    @click="startEdit(ev)"
                  >
                    Edit
                  </AppButton>
                  <AppButton
                    size="sm"
                    variant="danger"
                    :disabled="!session.accepting_evaluations || deleting === ev.id"
                    @click="handleDelete(ev.id)"
                  >
                    {{ deleting === ev.id ? '...' : 'Delete' }}
                  </AppButton>
                </template>
              </div>
            </td>
          </tr>
        </AppTable>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import type { MySession, UserResponse, QuestionResponse, TAEvaluationResponse, Marking } from '../../types/api'
import {
  getStudents,
  getQuestions,
  getEvaluations,
  createEvaluation,
  updateEvaluation,
  deleteEvaluation,
} from '../../api/ta'
import AppSpinner from '../common/AppSpinner.vue'
import AppBadge from '../common/AppBadge.vue'
import AppButton from '../common/AppButton.vue'
import AppTable from '../common/AppTable.vue'
import AppCombobox from '../common/AppCombobox.vue'
import AppSelect from '../common/AppSelect.vue'
import AppInput from '../common/AppInput.vue'

const props = defineProps<{ session: MySession }>()

const loading = ref(true)
const creating = ref(false)
const saving = ref(false)
const deleting = ref<number | null>(null)
const createError = ref('')

const students = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const evaluations = ref<TAEvaluationResponse[]>([])

// Create form
const form = ref<{
  student_id: number | null
  question_id: number | null
  marking: number | null
  remarks: string
}>({
  student_id: null,
  question_id: null,
  marking: null,
  remarks: '',
})

// Edit state
const editingId = ref<number | null>(null)
const editForm = ref<{ marking: number | null; remarks: string }>({ marking: null, remarks: '' })

// Derived
const studentOptions = computed(() =>
  students.value.map((s) => ({ value: s.id, label: `${s.name} (${s.email})` })),
)

const availableQuestions = computed(() => {
  if (form.value.student_id === null) return questions.value
  // Filter out questions already evaluated for this student
  const evaluatedQuestionIds = new Set(
    evaluations.value
      .filter((e) => e.student_id === form.value.student_id)
      .map((e) => e.question_id),
  )
  return questions.value.filter((q) => !evaluatedQuestionIds.has(q.id))
})

const canSubmit = computed(
  () =>
    form.value.student_id !== null &&
    form.value.question_id !== null &&
    form.value.marking !== null,
)

function studentName(id: number): string {
  return students.value.find((s) => s.id === id)?.name ?? String(id)
}

function questionText(id: number): string {
  return questions.value.find((q) => q.id === id)?.text ?? String(id)
}

function formatDate(dateStr: string): string {
  const d = new Date(dateStr)
  return d.toLocaleDateString(undefined, { year: 'numeric', month: 'long', day: 'numeric' })
}

async function handleCreate() {
  if (!canSubmit.value) return
  createError.value = ''
  creating.value = true
  try {
    const created = await createEvaluation(props.session.lab_session_id, {
      lab_session_id: props.session.lab_session_id,
      student_id: form.value.student_id as number,
      question_id: form.value.question_id as number,
      marking: form.value.marking as Marking,
      remarks: form.value.remarks || null,
    })
    evaluations.value.push(created)
    form.value = { student_id: form.value.student_id, question_id: null, marking: null, remarks: '' }
  } catch (e: unknown) {
    createError.value = e instanceof Error ? e.message : 'Failed to create evaluation.'
  } finally {
    creating.value = false
  }
}

function startEdit(ev: TAEvaluationResponse) {
  editingId.value = ev.id
  editForm.value = { marking: ev.marking, remarks: ev.remarks ?? '' }
}

function cancelEdit() {
  editingId.value = null
}

async function handleUpdate(id: number) {
  if (editForm.value.marking === null) return
  saving.value = true
  try {
    const updated = await updateEvaluation(props.session.lab_session_id, id, {
      marking: editForm.value.marking as Marking,
      remarks: editForm.value.remarks || null,
    })
    const idx = evaluations.value.findIndex((e) => e.id === id)
    if (idx !== -1) evaluations.value[idx] = updated
    editingId.value = null
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  deleting.value = id
  try {
    await deleteEvaluation(props.session.lab_session_id, id)
    evaluations.value = evaluations.value.filter((e) => e.id !== id)
  } finally {
    deleting.value = null
  }
}

onMounted(async () => {
  try {
    const [s, q, e] = await Promise.all([
      getStudents(props.session.lab_session_id),
      getQuestions(props.session.lab_session_id),
      getEvaluations(props.session.lab_session_id),
    ])
    students.value = s
    questions.value = q
    evaluations.value = e
  } finally {
    loading.value = false
  }
})
</script>
