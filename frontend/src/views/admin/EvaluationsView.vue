<!--
  EvaluationsView.vue (Admin)
  Admin can view, create, edit, and delete evaluations (override, unrestricted).
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Evaluations</h2>
        <p class="text-sm text-zinc-600 mt-1">Manage all evaluations (admin override)</p>
      </div>
      <div class="flex gap-2 self-start sm:self-auto shrink-0">
        <AppButton
          variant="secondary"
          :disabled="evaluations.length === 0"
          @click="downloadCsv"
          >Download CSV</AppButton
        >
        <AppButton @click="openCreate">Add Evaluation</AppButton>
      </div>
    </div>
    <!-- Subject Filter -->
    <div class="mb-4">
      <AppSelect
        v-model="filterSubjectId"
        label="Filter by Subject"
        class="max-w-xs"
        :disabled="loading"
      >
        <option value="">All Subjects</option>
        <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
          {{ subject.name }}
        </option>
      </AppSelect>
    </div>
    <div
      v-if="actionError"
      class="mb-4 p-3 bg-red-50 border border-red-200 rounded flex items-start justify-between gap-3"
    >
      <p class="text-sm text-red-700">{{ actionError }}</p>
      <button
        @click="actionError = ''"
        class="text-red-400 hover:text-red-600 transition-colors shrink-0"
        aria-label="Dismiss error"
      >
        <svg class="w-4 h-4" fill="none" stroke="currentColor" viewBox="0 0 24 24">
          <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M6 18L18 6M6 6l12 12" />
        </svg>
      </button>
    </div>
    <AppAsyncSection
      :loading="loading"
      :error="loadError"
      :has-content="evaluations.length > 0"
      loading-text="Loading evaluations..."
      @retry="load()"
    >
      <AppTable
        :isEmpty="filteredEvaluations.length === 0"
        emptyMessage="No evaluations found. Add your first evaluation or adjust your filters."
      >
        <template #head>
          <th>ID</th>
          <th>Student Email</th>
          <th>Subject</th>
          <th>Question</th>
          <th>TA</th>
          <th>Session</th>
          <th>Marking</th>
          <th>Remarks</th>
          <th>Actions</th>
        </template>
        <tr v-for="evaluation in filteredEvaluations" :key="evaluation.id">
          <td>{{ evaluation.id }}</td>
          <td>{{ getUserEmail(evaluation.student_id) }}</td>
          <td>{{ getQuestionSubject(evaluation.question_id) }}</td>
          <td>{{ getQuestionText(evaluation.question_id) }}</td>
          <td>{{ getUserName(evaluation.ta_id) }}</td>
          <td>{{ getSessionLabel(evaluation.lab_session_id) }}</td>
          <td v-if="editId !== evaluation.id">{{ evaluation.marking }} / 5</td>
          <td v-else>
            <AppSelect v-model.number="editMarking">
              <option v-for="n in 5" :key="n" :value="n">{{ n }} / 5</option>
            </AppSelect>
          </td>
          <td v-if="editId !== evaluation.id">{{ evaluation.remarks }}</td>
          <td v-else>
            <AppInput v-model="editRemarks" />
          </td>
          <td>
            <div class="flex gap-2">
              <AppButton
                v-if="editId !== evaluation.id"
                @click="startEdit(evaluation)"
                variant="secondary"
                size="sm"
                :disabled="rowBusy"
                >Edit</AppButton
              >
              <AppButton
                v-if="editId === evaluation.id"
                @click="saveEdit(evaluation.id)"
                variant="success"
                size="sm"
                :disabled="rowBusy"
                >{{ rowBusyKey === `save:${evaluation.id}` ? 'Saving...' : 'Save' }}</AppButton
              >
              <AppButton
                v-if="editId === evaluation.id"
                @click="cancelEdit"
                variant="ghost"
                size="sm"
                :disabled="rowBusy"
                >Cancel</AppButton
              >
              <AppButton
                variant="danger"
                size="sm"
                :disabled="rowBusy"
                @click="deleteEvaluationHandler(evaluation.id)"
                >{{
                  rowBusyKey === `delete:${evaluation.id}` ? 'Deleting...' : 'Delete'
                }}</AppButton
              >
            </div>
          </td>
        </tr>
      </AppTable>
    </AppAsyncSection>
    <!-- Create Modal -->
    <div
      v-if="showCreate"
      class="fixed inset-0 bg-black/50 backdrop-blur-sm flex items-center justify-center z-50 p-4"
    >
      <div
        class="bg-white p-6 rounded-lg shadow-xl w-full max-w-lg max-h-[90vh] overflow-auto animate-in fade-in zoom-in duration-200"
      >
        <div class="flex justify-between items-center mb-4">
          <h3 class="text-lg font-semibold text-zinc-900">Add Evaluation</h3>
          <button
            @click="showCreate = false"
            class="text-zinc-400 hover:text-zinc-600 transition-colors"
          >
            <svg class="w-5 h-5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
              <path
                stroke-linecap="round"
                stroke-linejoin="round"
                stroke-width="2"
                d="M6 18L18 6M6 6l12 12"
              />
            </svg>
          </button>
        </div>
        <AppSelect
          v-model="newLabSessionId"
          label="Lab Session"
          required
          class="mb-3"
        >
          <option :value="null">-- Select Lab Session --</option>
          <option v-for="session in labSessions" :key="session.id" :value="session.id">
            {{ getSessionLabel(session.id) }}
          </option>
        </AppSelect>
        <!-- Roster state, so "loading" and "nobody is on this roster" read differently -->
        <div v-if="newLabSessionId" class="mb-3">
          <AppSpinner v-if="rosterLoading" size="sm" text="Loading session roster..." />
          <p v-else-if="rosterError" class="text-sm text-red-600" role="alert">
            {{ rosterError }}
            <button class="underline hover:text-red-800" @click="loadRoster()">Retry</button>
          </p>
          <p v-else-if="sessionRoster.length === 0" class="text-sm text-zinc-500">
            No students or TAs are assigned to this session yet.
          </p>
        </div>
        <AppCombobox
          v-model="newStudentId"
          :options="sessionStudentOptions"
          :disabled="!newLabSessionId || rosterLoading"
          label="Student"
          placeholder="Search student by name or email..."
          required
          class="mb-3"
        />
        <AppCombobox
          v-model="newTaId"
          :options="sessionTaOptions"
          :disabled="!newLabSessionId || rosterLoading"
          label="TA"
          placeholder="Search TA by name or email..."
          required
          class="mb-3"
        />
        <AppSelect
          v-model="newQuestionId"
          :disabled="!newLabSessionId"
          label="Question"
          required
          class="mb-3"
        >
          <option :value="null">-- Select Question --</option>
          <option
            v-for="question in sessionQuestionOptions"
            :key="question.id"
            :value="question.id"
          >
            {{ question.text }}
          </option>
        </AppSelect>
        <AppSelect v-model.number="newMarking" label="Marking" required class="mb-3">
          <option v-for="n in 5" :key="n" :value="n">{{ n }} / 5</option>
        </AppSelect>
        <AppInput v-model="newRemarks" placeholder="Remarks (optional)" label="Remarks" />
        <p v-if="createError" class="text-sm text-red-600 mt-3">{{ createError }}</p>
        <div class="flex gap-2 mt-6 justify-end">
          <AppButton @click="showCreate = false" variant="ghost" :disabled="creating"
            >Cancel</AppButton
          >
          <AppButton @click="createEvaluationHandler" :disabled="creating">{{
            creating ? 'Creating...' : 'Create Evaluation'
          }}</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Evaluations CRUD view
import { ref, computed, watch } from 'vue'
import Papa from 'papaparse'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppCombobox from '../../components/common/AppCombobox.vue'
import AppAsyncSection from '../../components/common/AppAsyncSection.vue'
import AppSpinner from '../../components/common/AppSpinner.vue'
import AppTable from '../../components/common/AppTable.vue'
import {
  getEvaluations,
  createEvaluation,
  updateEvaluation,
  deleteEvaluation,
  getUsers,
  getQuestions,
  getSubjects,
  getLabSessions,
  getSessionAssignments,
} from '../../api/admin'
import type {
  EvaluationResponse,
  UserResponse,
  QuestionResponse,
  Marking,
  SubjectResponse,
  LabSession,
  SessionAssignment,
} from '../../types/api'
import { useAsyncAction, useAsyncTask } from '../../composables/useAsync'

const evaluations = ref<EvaluationResponse[]>([])
const users = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const subjects = ref<SubjectResponse[]>([])
const labSessions = ref<LabSession[]>([])
const showCreate = ref(false)
const newLabSessionId = ref<number | null>(null)
const newStudentId = ref<number | null>(null)
const newQuestionId = ref<number | null>(null)
const newTaId = ref<number | null>(null)
const newMarking = ref<Marking>(5)
const newRemarks = ref('')
const editId = ref<number | null>(null)
const editMarking = ref<Marking>(5)
const editRemarks = ref('')
const filterSubjectId = ref<number | string>('')

// Session roster for the create modal. Refetched on every session change, so
// a slow earlier response must not overwrite a newer one.
const sessionRoster = ref<SessionAssignment[]>([])
let latestRosterFetch = 0

const {
  loading,
  error: loadError,
  run: load,
  refresh,
} = useAsyncTask(
  async () => {
    ;[evaluations.value, users.value, questions.value, subjects.value, labSessions.value] =
      await Promise.all([
        getEvaluations(),
        getUsers(),
        getQuestions(),
        getSubjects(),
        getLabSessions(),
      ])
  },
  { immediate: true },
)

const {
  loading: rosterLoading,
  error: rosterError,
  run: loadRoster,
} = useAsyncTask(async () => {
  const call = ++latestRosterFetch
  const sessionId = newLabSessionId.value
  const roster = sessionId ? await getSessionAssignments(sessionId) : []
  if (call === latestRosterFetch) sessionRoster.value = roster
})

// Create is its own in-flight state (the modal button); edit/delete share one
// (only one row action can run at a time).
const { busy: creating, error: createError, run: runCreate } = useAsyncAction()
const {
  busy: rowBusy,
  busyKey: rowBusyKey,
  error: actionError,
  run: runRowAction,
} = useAsyncAction()

function getUserName(id: number) {
  return users.value.find((u) => u.id === id)?.name || ''
}

function getUserEmail(id: number) {
  return users.value.find((u) => u.id === id)?.email || ''
}
function getQuestionText(id: number) {
  return questions.value.find((q) => q.id === id)?.text || ''
}

function getQuestionSubject(questionId: number) {
  const question = questions.value.find((q) => q.id === questionId)
  if (!question) return ''
  return subjects.value.find((s) => s.id === question.subject_id)?.name || ''
}

function getSubjectName(id: number) {
  return subjects.value.find((s) => s.id === id)?.name || ''
}

function getSessionLabel(sessionId: number) {
  const session = labSessions.value.find((s) => s.id === sessionId)
  if (!session) return `Session #${sessionId}`
  return `${getSubjectName(session.subject_id)} — ${session.date}`
}

function getSessionDate(sessionId: number) {
  return labSessions.value.find((s) => s.id === sessionId)?.date || ''
}

// Export the FULL evaluation list (not the subject-filtered view) as a CSV,
// resolving foreign keys to human-readable values via the existing lookups.
function downloadCsv() {
  if (evaluations.value.length === 0) return
  const rows = evaluations.value.map((e) => ({
    'Evaluation ID': e.id,
    'Student Email': getUserEmail(e.student_id),
    'Student Name': getUserName(e.student_id),
    Subject: getQuestionSubject(e.question_id),
    Question: getQuestionText(e.question_id),
    'TA Email': getUserEmail(e.ta_id),
    'TA Name': getUserName(e.ta_id),
    'Session Date': getSessionDate(e.lab_session_id),
    Marking: e.marking,
    Remarks: e.remarks ?? '',
  }))
  const csv = Papa.unparse(rows)
  const filename = `evaluations-${new Date().toISOString().slice(0, 10)}.csv`
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = filename
  anchor.click()
  URL.revokeObjectURL(url)
}

const filteredEvaluations = computed(() => {
  if (filterSubjectId.value === '' || filterSubjectId.value === null) {
    return evaluations.value
  }
  return evaluations.value.filter((evaluation) => {
    const question = questions.value.find((q) => q.id === evaluation.question_id)
    return question?.subject_id === Number(filterSubjectId.value)
  })
})

// Roster-driven options for the create modal
const sessionStudentOptions = computed(() =>
  sessionRoster.value
    .filter((a) => a.role === 'student')
    .map((a) => {
      const u = users.value.find((user) => user.id === a.user_id)
      return { value: a.user_id, label: u ? `${u.name} (${u.email})` : String(a.user_id) }
    }),
)

const sessionTaOptions = computed(() =>
  sessionRoster.value
    .filter((a) => a.role === 'ta')
    .map((a) => {
      const u = users.value.find((user) => user.id === a.user_id)
      return { value: a.user_id, label: u ? `${u.name} (${u.email})` : String(a.user_id) }
    }),
)

const sessionQuestionOptions = computed(() => {
  if (!newLabSessionId.value) return []
  const session = labSessions.value.find((s) => s.id === newLabSessionId.value)
  if (!session) return []
  return questions.value.filter((q) => q.subject_id === session.subject_id)
})

// Reset dependent pickers + reload the roster whenever the session changes
// (watch, not @change, so programmatic changes are handled too).
watch(newLabSessionId, () => {
  newStudentId.value = null
  newTaId.value = null
  newQuestionId.value = null
  sessionRoster.value = []
  void loadRoster()
})

function openCreate() {
  createError.value = ''
  showCreate.value = true
}

async function createEvaluationHandler() {
  const labSessionId = newLabSessionId.value
  const studentId = newStudentId.value
  const questionId = newQuestionId.value
  const taId = newTaId.value
  if (!labSessionId || !studentId || !questionId || !taId || !newMarking.value) return
  await runCreate(async () => {
    await createEvaluation({
      lab_session_id: labSessionId,
      student_id: studentId,
      question_id: questionId,
      ta_id: taId,
      marking: newMarking.value,
      remarks: newRemarks.value || null,
    })
    newLabSessionId.value = null
    newStudentId.value = null
    newQuestionId.value = null
    newTaId.value = null
    newMarking.value = 5
    newRemarks.value = ''
    sessionRoster.value = []
    showCreate.value = false
  })
  // Silent: the table stays on screen instead of collapsing into a spinner.
  if (!createError.value) await refresh()
}

function startEdit(evaluation: EvaluationResponse) {
  editId.value = evaluation.id
  editMarking.value = evaluation.marking
  editRemarks.value = evaluation.remarks || ''
}

async function saveEdit(id: number) {
  const ev = evaluations.value.find((e) => e.id === id)
  if (!ev) return
  await runRowAction(async () => {
    await updateEvaluation(id, {
      lab_session_id: ev.lab_session_id,
      student_id: ev.student_id,
      question_id: ev.question_id,
      ta_id: ev.ta_id,
      marking: editMarking.value,
      remarks: editRemarks.value || null,
    })
    editId.value = null
    editMarking.value = 5
    editRemarks.value = ''
  }, `save:${id}`)
  if (!actionError.value) await refresh()
}

function cancelEdit() {
  editId.value = null
  editMarking.value = 5
  editRemarks.value = ''
}

async function deleteEvaluationHandler(id: number) {
  if (!confirm('Are you sure you want to delete this evaluation? This action cannot be undone.')) {
    return
  }
  await runRowAction(async () => {
    await deleteEvaluation(id)
  }, `delete:${id}`)
  if (!actionError.value) await refresh()
}
</script>
