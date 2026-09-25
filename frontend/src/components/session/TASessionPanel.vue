<!--
  TASessionPanel.vue
  Panel for TAs to view and manage evaluations within a session.
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
      This session is not accepting evaluations. All create, edit, and delete operations are
      disabled.
    </div>

    <AppAsyncSection
      :loading="loading"
      :error="error"
      :has-content="questions.length > 0"
      loading-text="Loading evaluations..."
      @retry="load()"
    >
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
              @open="pausePolling"
              @close="resumePolling"
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
          <p
            v-if="form.student_id !== null && availableQuestions.length === 0"
            class="text-sm text-zinc-500"
          >
            All questions for this student have already been evaluated.
          </p>
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
        <div class="px-6 py-4 border-b border-zinc-100 flex items-center justify-between">
          <h3 class="text-base font-semibold text-zinc-900">My Evaluations</h3>
          <p v-if="updateError || deleteError" class="text-sm text-red-600">{{ updateError || deleteError }}</p>
        </div>
        <AppTable :isEmpty="evaluations.length === 0" emptyMessage="No evaluations yet.">
          <template #head>
            <th>Student Email</th>
            <th>Question</th>
            <th>Marking</th>
            <th>Remarks</th>
            <th>Actions</th>
          </template>
          <tr v-for="ev in evaluations" :key="ev.id">
            <td>{{ studentEmail(ev.student_id) }}</td>
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
    </AppAsyncSection>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import type {
  MySession,
  UserResponse,
  QuestionResponse,
  TAEvaluationResponse,
  TAEvaluationCoverage,
  Marking,
} from '../../types/api'
import {
  getStudents,
  getQuestions,
  getEvaluations,
  getCoverage,
  createEvaluation,
  updateEvaluation,
  deleteEvaluation,
} from '../../api/ta'
import AppAsyncSection from '../common/AppAsyncSection.vue'
import AppBadge from '../common/AppBadge.vue'
import AppButton from '../common/AppButton.vue'
import AppTable from '../common/AppTable.vue'
import AppCombobox from '../common/AppCombobox.vue'
import AppSelect from '../common/AppSelect.vue'
import AppInput from '../common/AppInput.vue'
import AppPollStatus from '../common/AppPollStatus.vue'
import { useAsyncTask } from '../../composables/useAsync'
import { usePolling, type PollContext } from '../../composables/usePolling'
import { formatDate } from '@/utils/date'
import { apiErrorMessage } from '@/utils/errors'

const props = defineProps<{ session: MySession }>()

const creating = ref(false)
const saving = ref(false)
const deleting = ref<number | null>(null)
const createError = ref('')
const updateError = ref('')
const deleteError = ref('')

const students = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const evaluations = ref<TAEvaluationResponse[]>([])
// Every (student, question) pair already evaluated on this session by ANY
// TA — drives the question list so two TAs can't be offered the same pair.
const coverage = ref<TAEvaluationCoverage[]>([])

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

// Reset the question/marks when the student changes: the question list is
// filtered per student, so a stale question_id could be already-evaluated
// for the newly selected student and get rejected (400) on submit.
watch(
  () => form.value.student_id,
  () => {
    form.value.question_id = null
    form.value.marking = null
    form.value.remarks = ''
  },
)

// Edit state
const editingId = ref<number | null>(null)
const editForm = ref<{ marking: number | null; remarks: string }>({ marking: null, remarks: '' })

// Derived
const studentOptions = computed(() =>
  students.value.map((s) => ({ value: s.id, label: `${s.name} (${s.email})` })),
)

const availableQuestions = computed(() => {
  if (form.value.student_id === null) return questions.value
  // Filter out questions already evaluated for this student by any TA
  const evaluatedQuestionIds = new Set(
    coverage.value.filter((e) => e.student_id === form.value.student_id).map((e) => e.question_id),
  )
  return questions.value.filter((q) => !evaluatedQuestionIds.has(q.id))
})

const canSubmit = computed(
  () =>
    form.value.student_id !== null &&
    form.value.question_id !== null &&
    form.value.marking !== null,
)

function studentEmail(id: number): string {
  return students.value.find((s) => s.id === id)?.email ?? String(id)
}

function questionText(id: number): string {
  return questions.value.find((q) => q.id === id)?.text ?? String(id)
}

async function handleCreate() {
  if (!canSubmit.value) return
  polling.invalidate()
  createError.value = ''
  updateError.value = ''
  deleteError.value = ''
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
    coverage.value.push({
      student_id: created.student_id,
      question_id: created.question_id,
      ta_id: created.ta_id,
    })
    form.value = { student_id: form.value.student_id, question_id: null, marking: null, remarks: '' }
  } catch (e: unknown) {
    // apiErrorMessage yields '' for a cancelled request, so a silent
    // session expiry redirects without flashing a banner.
    createError.value = apiErrorMessage(e, 'Failed to create evaluation.')
    // Another TA may have taken this pair since the page loaded; resync so
    // the question list reflects what is actually still available.
    await refreshCoverage()
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
  polling.invalidate()
  createError.value = ''
  updateError.value = ''
  deleteError.value = ''
  saving.value = true
  try {
    const updated = await updateEvaluation(props.session.lab_session_id, id, {
      marking: editForm.value.marking as Marking,
      remarks: editForm.value.remarks || null,
    })
    const idx = evaluations.value.findIndex((e) => e.id === id)
    if (idx !== -1) evaluations.value[idx] = updated
    editingId.value = null
  } catch (e: unknown) {
    // apiErrorMessage yields '' for a cancelled request, so a silent
    // session expiry redirects without flashing a banner.
    updateError.value = apiErrorMessage(e, 'Failed to update evaluation.')
  } finally {
    saving.value = false
  }
}

async function handleDelete(id: number) {
  if (!confirm('Are you sure you want to delete this evaluation? This action cannot be undone.')) {
    return
  }
  polling.invalidate()
  createError.value = ''
  updateError.value = ''
  deleteError.value = ''
  deleting.value = id
  try {
    const removed = evaluations.value.find((e) => e.id === id)
    await deleteEvaluation(props.session.lab_session_id, id)
    evaluations.value = evaluations.value.filter((e) => e.id !== id)
    if (removed) {
      coverage.value = coverage.value.filter(
        (c) => !(c.student_id === removed.student_id && c.question_id === removed.question_id),
      )
    }
  } catch (e: unknown) {
    // apiErrorMessage yields '' for a cancelled request, so a silent
    // session expiry redirects without flashing a banner.
    deleteError.value = apiErrorMessage(e, 'Failed to delete evaluation.')
  } finally {
    deleting.value = null
  }
}

async function refreshCoverage() {
  try {
    coverage.value = await getCoverage(props.session.lab_session_id)
  } catch {
    // Non-fatal: keep the current view rather than blanking the form.
  }
}

// The roster and the question bank do not change on a grading timescale, so
// they load once on mount rather than on every poll tick.
async function loadStatic() {
  const [s, q] = await Promise.all([
    getStudents(props.session.lab_session_id),
    getQuestions(props.session.lab_session_id),
  ])
  students.value = s
  questions.value = q
}

// The live half: what other TAs have graded. This is the poll target.
async function loadLive(ctx?: PollContext) {
  const [e, c] = await Promise.all([
    getEvaluations(props.session.lab_session_id, ctx?.signal),
    getCoverage(props.session.lab_session_id, ctx?.signal),
  ])
  if (ctx?.isStale()) return
  evaluations.value = e
  coverage.value = c
}

// If the selected student leaves the roster, `AppCombobox` renders an empty
// input while `student_id` still points at them — the TA would submit against
// an invisible student. Clear the field and say why.
watch(studentOptions, (options) => {
  const selected = form.value.student_id
  if (selected === null) return
  if (options.some((o) => o.value === selected)) return
  form.value.student_id = null
  createError.value = 'The selected student is no longer on this session roster.'
})

const {
  loading,
  error,
  run: load,
} = useAsyncTask(
  async () => {
    await Promise.all([loadStatic(), loadLive()])
  },
  { immediate: true },
)

// Several TAs grade one session at the same time, so coverage (which questions
// are still free) and the evaluation list have to keep up. Suspended whenever
// the user is committed to a form: an inline edit, a request in flight, or a
// create form filled past the student picker — a refetch there would either
// discard their typing or shrink `availableQuestions` under their choice.
//
// Polls the raw loader, not the task's refresh(): usePolling swallows a failed
// tick, where useAsyncTask would publish it into `error` and blank the panel
// behind a banner.
const polling = usePolling(loadLive, {
  paused: () =>
    editingId.value !== null ||
    creating.value ||
    saving.value ||
    deleting.value !== null ||
    // Picking a student is already commitment: from here on the question list
    // is filtered for that student and must not shift under the TA.
    form.value.student_id !== null ||
    form.value.question_id !== null ||
    form.value.marking !== null ||
    form.value.remarks !== '',
})
const pollStatus = polling.statusText

// The student picker's dropdown is open state no `paused` getter can see.
function pausePolling() {
  polling.pause()
}

function resumePolling() {
  polling.resume()
}
</script>
