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
          :disabled="filteredEvaluations.length === 0"
          @click="downloadCsv"
          >Download CSV ({{ filteredEvaluations.length }})</AppButton
        >
        <AppButton @click="openCreate">Add Evaluation</AppButton>
      </div>
    </div>
    <!-- Filters + sort. All filters compose (AND); the result is sorted and
         then paginated client-side by the "Show more" control below. -->
    <div class="mb-4 flex flex-col gap-3 sm:flex-row sm:flex-wrap sm:items-end">
      <AppSelect
        v-model="filterSubjectId"
        label="Filter by Subject"
        class="min-w-48 sm:max-w-xs sm:grow sm:basis-56"
      >
        <option value="">All Subjects</option>
        <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
          {{ subject.name }}
        </option>
      </AppSelect>
      <AppSelect
        v-model="filterSessionId"
        label="Filter by Slot"
        class="min-w-48 sm:max-w-xs sm:grow sm:basis-56"
      >
        <option value="">All Slots</option>
        <option v-for="session in sessionFilterOptions" :key="session.id" :value="session.id">
          {{ getSessionLabel(session.id) }}
        </option>
      </AppSelect>
      <AppInput
        v-model="studentEmailQuery"
        label="Filter by Student Email"
        placeholder="Search student email..."
        class="min-w-48 sm:max-w-xs sm:grow sm:basis-56"
      />
      <AppSelect v-model="sortKey" label="Sort by" class="min-w-48 sm:max-w-xs sm:grow sm:basis-56">
        <option value="session_desc">Slot date — newest first</option>
        <option value="session_asc">Slot date — oldest first</option>
        <option value="id_desc">Evaluation ID — newest first</option>
        <option value="id_asc">Evaluation ID — oldest first</option>
      </AppSelect>
      <AppButton v-if="hasActiveFilters" variant="ghost" @click="clearFilters"
        >Clear filters</AppButton
      >
    </div>
    <p class="mb-3 text-sm text-zinc-600">{{ countSummary }}</p>
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
          <path
            stroke-linecap="round"
            stroke-linejoin="round"
            stroke-width="2"
            d="M6 18L18 6M6 6l12 12"
          />
        </svg>
      </button>
    </div>
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
      <tr v-for="evaluation in visibleEvaluations" :key="evaluation.id">
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
              >Edit</AppButton
            >
            <AppButton
              v-if="editId === evaluation.id"
              @click="saveEdit(evaluation.id)"
              variant="success"
              size="sm"
              >Save</AppButton
            >
            <AppButton v-if="editId === evaluation.id" @click="cancelEdit" variant="ghost" size="sm"
              >Cancel</AppButton
            >
            <AppButton variant="danger" size="sm" @click="deleteEvaluationHandler(evaluation.id)"
              >Delete</AppButton
            >
          </div>
        </td>
      </tr>
    </AppTable>
    <!-- Front-end pagination: keeps the rendered row count bounded, and is
         reversible so an accumulated DOM can be collapsed without having to
         touch a filter. -->
    <div v-if="hasMore || canShowLess" class="mt-4 flex flex-wrap justify-center gap-2">
      <AppButton v-if="hasMore" variant="secondary" @click="showMore">
        Show more ({{ remainingCount }} remaining)
      </AppButton>
      <AppButton v-if="canShowAll" variant="secondary" @click="showAll">
        Show all {{ filteredEvaluations.length }}
      </AppButton>
      <AppButton v-if="canShowLess" variant="ghost" @click="showLess">
        Show less (first {{ PAGE_SIZE }})
      </AppButton>
    </div>
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
        <AppCombobox
          v-model="newStudentId"
          :options="sessionStudentOptions"
          :disabled="!newLabSessionId || sessionRosterLoading"
          label="Student"
          placeholder="Search student by name or email..."
          required
          class="mb-3"
        />
        <AppCombobox
          v-model="newTaId"
          :options="sessionTaOptions"
          :disabled="!newLabSessionId || sessionRosterLoading"
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
          <AppButton @click="showCreate = false" variant="ghost">Cancel</AppButton>
          <AppButton @click="createEvaluationHandler">Create Evaluation</AppButton>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
// Admin Evaluations CRUD view
import { ref, onMounted, onUnmounted, computed, watch } from 'vue'
import Papa from 'papaparse'
import AppButton from '../../components/common/AppButton.vue'
import AppInput from '../../components/common/AppInput.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppCombobox from '../../components/common/AppCombobox.vue'
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
import { apiErrorMessage } from '../../utils/errors'

const evaluations = ref<EvaluationResponse[]>([])
const users = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const subjects = ref<SubjectResponse[]>([])
const labSessions = ref<LabSession[]>([])
const showCreate = ref(false)
const createError = ref('')
const actionError = ref('')
const newLabSessionId = ref<number | null>(null)
const newStudentId = ref<number | null>(null)
const newQuestionId = ref<number | null>(null)
const newTaId = ref<number | null>(null)
const newMarking = ref<Marking>(5)
const newRemarks = ref('')
const editId = ref<number | null>(null)
const editMarking = ref<Marking>(5)
const editRemarks = ref('')
// `''` is only the initial value: AppSelect emits `null` for its empty
// option, so a filter the user has touched and reset back to "All" is null,
// never `''`. Both mean "no filter" — `isBlank` below is the single place
// that knows that, and every emptiness test goes through it.
const filterSubjectId = ref<number | string | null>('')
const filterSessionId = ref<number | string | null>('')
// Raw input (bound to the field) vs debounced value (drives the filter chain),
// so typing doesn't re-filter the whole array on every keystroke.
const studentEmailQuery = ref('')
const debouncedEmailQuery = ref('')
// A plain string (not a union) because AppSelect emits `string | number | null`;
// the comparator falls back to the default order for any unknown value.
const sortKey = ref<string>('session_desc')

// How many rows are rendered at a time ("Show more" adds another page).
const PAGE_SIZE = 100
// Below this many filtered rows, offer a single "Show all" instead of making
// the admin click through pages.
const SHOW_ALL_THRESHOLD = 500
const visibleCount = ref(PAGE_SIZE)

const isBlank = (value: unknown) => value === '' || value === null

// Session roster state for the create modal
const sessionRoster = ref<SessionAssignment[]>([])
const sessionRosterLoading = ref(false)

async function load() {
  ;[evaluations.value, users.value, questions.value, subjects.value, labSessions.value] =
    await Promise.all([
      getEvaluations(),
      getUsers(),
      getQuestions(),
      getSubjects(),
      getLabSessions(),
    ])
}
onMounted(load)

// Id -> row lookups. The table resolves several foreign keys per row, so a
// linear `find()` per cell is O(rows x lookups); these maps keep it O(1).
const usersById = computed(() => new Map(users.value.map((u) => [u.id, u])))
const questionsById = computed(() => new Map(questions.value.map((q) => [q.id, q])))
const subjectsById = computed(() => new Map(subjects.value.map((s) => [s.id, s])))
const sessionsById = computed(() => new Map(labSessions.value.map((s) => [s.id, s])))

function getUserName(id: number) {
  return usersById.value.get(id)?.name || ''
}

function getUserEmail(id: number) {
  return usersById.value.get(id)?.email || ''
}
function getQuestionText(id: number) {
  return questionsById.value.get(id)?.text || ''
}

function getQuestionSubject(questionId: number) {
  const question = questionsById.value.get(questionId)
  if (!question) return ''
  return subjectsById.value.get(question.subject_id)?.name || ''
}

function getSubjectName(id: number) {
  return subjectsById.value.get(id)?.name || ''
}

function getSessionLabel(sessionId: number) {
  const session = sessionsById.value.get(sessionId)
  if (!session) return `Session #${sessionId}`
  return `${getSubjectName(session.subject_id)} — ${session.date}`
}

function getSessionDate(sessionId: number) {
  return sessionsById.value.get(sessionId)?.date || ''
}

// Export the currently filtered (but NOT paginated) list as a CSV, in the
// order shown — the filters are the admin's way of scoping the export, and
// the button label carries the row count so it's clear what's included.
// Foreign keys are resolved to human-readable values via the existing lookups.
function downloadCsv() {
  if (filteredEvaluations.value.length === 0) return
  const rows = filteredEvaluations.value.map((e) => ({
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
  const url = URL.createObjectURL(new Blob([csv], { type: 'text/csv;charset=utf-8;' }))
  const anchor = document.createElement('a')
  anchor.href = url
  anchor.download = csvFilename()
  anchor.click()
  URL.revokeObjectURL(url)
}

function slugify(value: string) {
  return value
    .toLowerCase()
    .replace(/[^a-z0-9]+/g, '-')
    .replace(/^-+|-+$/g, '')
}

// The export is scoped to the active filters, so the filename carries that
// scope: a one-slot export stays distinguishable from a full one after it has
// been downloaded or mailed on.
function csvFilename() {
  const parts = ['evaluations']
  const subject = isBlank(filterSubjectId.value)
    ? ''
    : slugify(getSubjectName(Number(filterSubjectId.value)))
  if (subject) parts.push(subject)
  const slotDate = isBlank(filterSessionId.value)
    ? ''
    : getSessionDate(Number(filterSessionId.value))
  if (slotDate) parts.push(slotDate)
  if (hasActiveFilters.value) parts.push('filtered')
  parts.push(new Date().toISOString().slice(0, 10))
  return `${parts.join('-')}.csv`
}

// --- Filter / sort / paginate pipeline ---------------------------------
// Each stage is its own computed so a change to one filter only re-runs that
// stage and the ones after it, and "Show more" re-runs none of them.

const subjectFiltered = computed(() => {
  if (isBlank(filterSubjectId.value)) {
    return evaluations.value
  }
  const subjectId = Number(filterSubjectId.value)
  return evaluations.value.filter(
    (evaluation) => questionsById.value.get(evaluation.question_id)?.subject_id === subjectId,
  )
})

const sessionFiltered = computed(() => {
  if (isBlank(filterSessionId.value)) {
    return subjectFiltered.value
  }
  const sessionId = Number(filterSessionId.value)
  return subjectFiltered.value.filter((evaluation) => evaluation.lab_session_id === sessionId)
})

const emailFiltered = computed(() => {
  const query = debouncedEmailQuery.value
  if (!query) return sessionFiltered.value
  return sessionFiltered.value.filter((evaluation) => {
    const student = usersById.value.get(evaluation.student_id)
    // Users missing from the lookup would silently never match an email
    // query, so fall back to their raw id — they stay findable.
    const haystack = student ? student.email.toLowerCase() : `#${evaluation.student_id}`
    return haystack.includes(query)
  })
})

// Sorted view of the filtered set. Every comparator tie-breaks on id, so the
// order is total and stable (rows never jitter between recomputes).
const filteredEvaluations = computed(() => {
  const rows = emailFiltered.value
  if (sortKey.value === 'id_asc') return rows.slice().sort((a, b) => a.id - b.id)
  if (sortKey.value === 'id_desc') return rows.slice().sort((a, b) => b.id - a.id)
  const direction = sortKey.value === 'session_asc' ? 1 : -1
  // Decorate-sort-undecorate: resolve each row's slot date ONCE (n lookups)
  // rather than twice per comparison (~2 n log n lookups) — the comparator
  // itself then only compares two already-resolved primitives.
  const decorated = rows.map((row) => ({
    row,
    // Session dates are ISO strings, so a plain compare is chronological.
    date: getSessionDate(row.lab_session_id),
  }))
  decorated.sort((a, b) => {
    if (a.date !== b.date) return a.date < b.date ? -direction : direction
    return (a.row.id - b.row.id) * direction
  })
  return decorated.map((entry) => entry.row)
})

const visibleEvaluations = computed(() => filteredEvaluations.value.slice(0, visibleCount.value))

// "matching" only makes sense when something is actually filtering.
const countSummary = computed(() => {
  const total = filteredEvaluations.value.length
  const noun = hasActiveFilters.value ? 'matching evaluations' : 'evaluations'
  const base = `Showing ${visibleEvaluations.value.length} of ${total} ${noun}`
  if (total === evaluations.value.length) return base
  return `${base} (${evaluations.value.length} in total)`
})

const hasMore = computed(() => visibleCount.value < filteredEvaluations.value.length)

const remainingCount = computed(
  () => filteredEvaluations.value.length - visibleEvaluations.value.length,
)

// "Show all" is only offered while the whole filtered set is small enough to
// render without the lag this pagination exists to avoid.
const canShowAll = computed(
  () => hasMore.value && filteredEvaluations.value.length <= SHOW_ALL_THRESHOLD,
)

const canShowLess = computed(() => visibleCount.value > PAGE_SIZE)

function showMore() {
  visibleCount.value += PAGE_SIZE
}

function showAll() {
  visibleCount.value = filteredEvaluations.value.length
}

function showLess() {
  visibleCount.value = PAGE_SIZE
  // An in-progress edit on a row we just collapsed away would be stranded:
  // not rendered, so neither saveable nor cancellable.
  if (editId.value !== null && !visibleEvaluations.value.some((e) => e.id === editId.value)) {
    cancelEdit()
  }
}

// Slot options narrow to the selected subject; newest slot first so the
// current one is at the top.
const sessionFilterOptions = computed(() => {
  const subjectId = isBlank(filterSubjectId.value) ? null : Number(filterSubjectId.value)
  return labSessions.value
    .filter((session) => subjectId === null || session.subject_id === subjectId)
    .slice()
    .sort((a, b) => (a.date === b.date ? b.id - a.id : a.date < b.date ? 1 : -1))
})

const hasActiveFilters = computed(
  () =>
    !isBlank(filterSubjectId.value) ||
    !isBlank(filterSessionId.value) ||
    // Trimmed, to agree with the debounced value that actually filters:
    // a whitespace-only query filters nothing, so it isn't an active filter.
    studentEmailQuery.value.trim() !== '',
)

function clearFilters() {
  filterSubjectId.value = ''
  filterSessionId.value = ''
  studentEmailQuery.value = ''
  debouncedEmailQuery.value = ''
}

// Debounce the email box so a large array isn't re-filtered per keystroke.
let emailDebounceTimer: ReturnType<typeof setTimeout> | undefined
watch(studentEmailQuery, (value) => {
  clearTimeout(emailDebounceTimer)
  emailDebounceTimer = setTimeout(() => {
    debouncedEmailQuery.value = value.trim().toLowerCase()
  }, 250)
})
onUnmounted(() => clearTimeout(emailDebounceTimer))

// Drop a slot selection that no longer belongs to the selected subject.
watch(filterSubjectId, () => {
  if (isBlank(filterSessionId.value) || isBlank(filterSubjectId.value)) return
  const session = sessionsById.value.get(Number(filterSessionId.value))
  if (!session || session.subject_id !== Number(filterSubjectId.value)) {
    filterSessionId.value = ''
  }
})

// Any change to the result set or its order restarts pagination, otherwise
// the offset would be stale against a different list. An in-progress inline
// edit is dropped at the same time: its row may no longer be rendered, which
// leaves the edit unsaveable, uncancellable, and liable to reappear with
// stale values if the filter is later widened again.
watch([filterSubjectId, filterSessionId, debouncedEmailQuery, sortKey], () => {
  visibleCount.value = PAGE_SIZE
  cancelEdit()
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
  onSessionChange()
})

async function onSessionChange() {
  // Reset dependent pickers when session changes
  newStudentId.value = null
  newTaId.value = null
  newQuestionId.value = null
  sessionRoster.value = []
  if (!newLabSessionId.value) return
  sessionRosterLoading.value = true
  try {
    sessionRoster.value = await getSessionAssignments(newLabSessionId.value)
  } finally {
    sessionRosterLoading.value = false
  }
}

function openCreate() {
  createError.value = ''
  showCreate.value = true
}

async function createEvaluationHandler() {
  if (
    !newLabSessionId.value ||
    !newStudentId.value ||
    !newQuestionId.value ||
    !newTaId.value ||
    !newMarking.value
  )
    return
  createError.value = ''
  try {
    await createEvaluation({
      lab_session_id: newLabSessionId.value,
      student_id: newStudentId.value,
      question_id: newQuestionId.value,
      ta_id: newTaId.value,
      marking: newMarking.value,
      remarks: newRemarks.value || null,
    })
  } catch (e) {
    createError.value = apiErrorMessage(e)
    return
  }
  newLabSessionId.value = null
  newStudentId.value = null
  newQuestionId.value = null
  newTaId.value = null
  newMarking.value = 5
  newRemarks.value = ''
  sessionRoster.value = []
  showCreate.value = false
  await load()
}

function startEdit(evaluation: EvaluationResponse) {
  editId.value = evaluation.id
  editMarking.value = evaluation.marking
  editRemarks.value = evaluation.remarks || ''
}

async function saveEdit(id: number) {
  const ev = evaluations.value.find((e) => e.id === id)
  if (!ev) return
  actionError.value = ''
  try {
    await updateEvaluation(id, {
      lab_session_id: ev.lab_session_id,
      student_id: ev.student_id,
      question_id: ev.question_id,
      ta_id: ev.ta_id,
      marking: editMarking.value,
      remarks: editRemarks.value || null,
    })
  } catch (e) {
    actionError.value = apiErrorMessage(e)
    return
  }
  editId.value = null
  editMarking.value = 5
  editRemarks.value = ''
  await load()
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
  actionError.value = ''
  try {
    await deleteEvaluation(id)
  } catch (e) {
    actionError.value = apiErrorMessage(e)
    return
  }
  await load()
}
</script>
