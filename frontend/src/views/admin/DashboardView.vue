<!--
  DashboardView.vue (Admin)
  Per-slot analytics: TA workload and marking spread, student coverage
  (including students nobody has evaluated yet) and the spread of marks each
  student received. Every list is fetched once and every statistic is derived
  client-side from chained computeds - there are no aggregation endpoints
  behind this page, which is also why it is an opt-in tab rather than the
  admin landing page.
-->
<template>
  <div>
    <div class="flex flex-col gap-4 sm:flex-row sm:justify-between sm:items-center mb-6">
      <div>
        <h2 class="text-2xl font-bold text-zinc-900">Dashboard</h2>
        <p class="text-sm text-zinc-600 mt-1">
          Evaluation coverage and marking spread for a single lab slot.
        </p>
      </div>
      <div class="flex items-center gap-3 self-start sm:self-auto shrink-0">
        <!-- A snapshot, not a live view: say when it was taken. -->
        <span v-if="lastUpdatedLabel" class="text-sm text-zinc-500 tabular-nums">
          as of {{ lastUpdatedLabel }}
        </span>
        <AppButton variant="secondary" :disabled="loading || refreshing" @click="refresh">
          {{ refreshing ? 'Refreshing…' : 'Refresh' }}
        </AppButton>
      </div>
    </div>

    <!-- Slot picker -->
    <div class="mb-6 grid gap-3 sm:grid-cols-2 lg:max-w-3xl">
      <AppSelect v-model="filterSubjectId" label="Subject">
        <option :value="null">All subjects</option>
        <option v-for="subject in subjects" :key="subject.id" :value="subject.id">
          {{ subject.name }}
        </option>
      </AppSelect>
      <AppSelect
        v-model="selectedSessionId"
        label="Lab slot"
        :hint="selectableSessions.length === 0 ? 'No lab slots match this subject.' : undefined"
      >
        <option :value="null">-- Select a lab slot --</option>
        <option v-for="slot in selectableSessions" :key="slot.id" :value="slot.id">
          {{ sessionLabel(slot) }}
        </option>
      </AppSelect>
    </div>

    <div
      v-if="loadError"
      class="mb-4 p-3 bg-red-50 border border-red-200 rounded flex items-start justify-between gap-3"
    >
      <p class="text-sm text-red-700">{{ loadError }}</p>
      <button
        @click="loadError = ''"
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

    <div v-if="loading" class="py-16">
      <AppSpinner size="lg" centered text="Loading dashboard data..." />
    </div>

    <div
      v-else-if="labSessions.length === 0"
      class="rounded-lg border border-zinc-200 bg-white p-10 text-center shadow-sm"
    >
      <h3 class="text-sm font-medium text-zinc-900">No lab slots yet</h3>
      <p class="mt-1 text-sm text-zinc-500">
        Create a lab session first — the dashboard reports on one slot at a time.
      </p>
    </div>

    <div
      v-else-if="!selectedSession"
      class="rounded-lg border border-zinc-200 bg-white p-10 text-center shadow-sm"
    >
      <h3 class="text-sm font-medium text-zinc-900">Pick a lab slot</h3>
      <p class="mt-1 text-sm text-zinc-500">Choose a slot above to see its statistics.</p>
    </div>

    <template v-else>
      <!-- Overview -->
      <section class="mb-8" aria-labelledby="overview-heading">
        <h3 id="overview-heading" class="text-lg font-semibold text-zinc-900 mb-3">
          {{ sessionLabel(selectedSession) }}
        </h3>
        <div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-4">
          <div class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <p class="text-sm font-medium text-zinc-600">Evaluation coverage</p>
            <p class="mt-1 text-5xl font-semibold text-zinc-900 leading-none">
              {{ coverageLabel }}
            </p>
            <p class="mt-2 text-sm text-zinc-500">
              {{ countedEvaluations }} of {{ expectedTotal }} expected
              <span v-if="expectedTotal === 0">(no questions on this subject yet)</span>
              <span v-else
                >({{ rosterStudents.length }} students × {{ sessionQuestions.length }} questions)</span
              >
            </p>
          </div>
          <div
            class="rounded-lg border bg-white p-5 shadow-sm"
            :class="pendingStudents.length > 0 ? 'border-red-200' : 'border-zinc-200'"
          >
            <p class="text-sm font-medium text-zinc-600">Not yet evaluated</p>
            <p
              class="mt-1 text-5xl font-semibold leading-none"
              :class="pendingStudents.length > 0 ? 'text-red-700' : 'text-zinc-900'"
            >
              {{ pendingStudents.length }}
            </p>
            <p class="mt-2 text-sm text-zinc-500">
              student{{ pendingStudents.length === 1 ? '' : 's' }} with no evaluation at all
            </p>
          </div>
          <div class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <p class="text-sm font-medium text-zinc-600">Roster</p>
            <p class="mt-1 text-2xl font-semibold text-zinc-900">
              {{ rosterStudents.length }} on roster
              <span v-if="offRosterStudents > 0" class="text-base font-normal text-zinc-500">
                (+{{ offRosterStudents }} off-roster)
              </span>
            </p>
            <p class="mt-1 text-sm text-zinc-500">
              {{ rosterTas.length }} TAs assigned
              <span v-if="offRosterTas > 0">(+{{ offRosterTas }} off-roster)</span>
            </p>
          </div>
          <div class="rounded-lg border border-zinc-200 bg-white p-5 shadow-sm">
            <p class="text-sm font-medium text-zinc-600">Mean marking</p>
            <p class="mt-1 text-2xl font-semibold text-zinc-900">
              {{ formatMean(sessionMean) }}
            </p>
            <p class="mt-1 text-sm text-zinc-500">
              across {{ sessionEvaluations.length }} evaluation{{
                sessionEvaluations.length === 1 ? '' : 's'
              }}
            </p>
          </div>
        </div>
      </section>

      <!-- The one thing to act on mid-lab, directly under the numbers. -->
      <div
        v-if="pendingStudents.length > 0"
        class="mb-8 rounded-lg border border-red-200 bg-red-50 p-4"
      >
        <h3 class="text-sm font-semibold text-red-900">
          {{ pendingStudents.length }} student{{
            pendingStudents.length === 1 ? ' has' : 's have'
          }}
          no evaluations yet
        </h3>
        <ul class="mt-2 flex flex-wrap gap-2">
          <li v-for="student in pendingStudents" :key="student.id">
            <AppBadge variant="danger" size="sm">{{ student.name }}</AppBadge>
          </li>
        </ul>
      </div>

      <!-- No evaluations at all: everything below the roster view is moot -->
      <div
        v-if="sessionEvaluations.length === 0"
        class="mb-8 rounded-lg border border-amber-200 bg-amber-50 p-5"
      >
        <h3 class="text-sm font-semibold text-amber-900">No evaluations recorded yet</h3>
        <p class="mt-1 text-sm text-amber-800">
          Marking-spread charts appear once the first evaluation is submitted. The rosters below
          show who is still waiting.
        </p>
      </div>

      <PersonStatsPanel
        heading="TA activity"
        heading-id="ta-heading"
        description="How much each TA graded, and how leniently they marked."
        :rows="taStats"
        person-label="TA"
        count-label="Evaluations"
        empty-title="No TAs on this slot"
        empty-message="Assign a TA to the session roster first."
        show-count-chart
        count-chart-heading="Evaluations per TA"
        count-chart-caption="A TA who has graded nothing shows a red stub at zero."
        stacked-mode="percent"
        marks-chart-heading="Marks allotted per TA (share of their evaluations)"
        marks-chart-caption="Normalised to 100% so TAs with different workloads stay comparable. Hover a segment for the raw count."
        show-mean-chart
        mean-chart-heading="Mean mark per TA"
        mean-chart-caption="Each dot is one TA's mean on the 1–5 scale; the dashed line is the slot mean. A dot well off the line is a TA marking harder or softer than the rest."
        :mean-reference="sessionMean"
        show-students-covered
        show-shares
      />

      <PersonStatsPanel
        heading="Student coverage"
        heading-id="student-heading"
        description="Every student on the roster, including those with no evaluations at all."
        :rows="studentStats"
        person-label="Student"
        count-label="Received"
        empty-title="No students on this slot"
        empty-message="Add students to the session roster first."
        stacked-mode="count"
        marks-chart-heading="Marks received per student"
        marks-chart-caption="Raw counts, so bar length also shows how much a student has been graded. Sorted fewest first; students with nothing recorded have a red name label and sit at the top."
        :expected-per-person="sessionQuestions.length"
      />

      <!-- Context, not an answer: the slot-wide baseline the TA panel compares against. -->
      <section
        v-if="sessionEvaluations.length > 0"
        class="mb-8 rounded-lg border border-zinc-200 bg-white p-5 shadow-sm"
        aria-labelledby="session-marks-heading"
      >
        <h3 id="session-marks-heading" class="text-lg font-semibold text-zinc-900">
          Marks awarded in this slot
        </h3>
        <p class="text-sm text-zinc-600 mt-1 mb-4">
          The baseline every TA above is compared against.
        </p>
        <BaseChart
          type="bar"
          :data="sessionMarksData"
          :options="sessionMarksOptions"
          :height="240"
          chart-label="Bar chart of how many evaluations were given each marking from 1 to 5; the counts are listed below the chart."
        />
        <p class="mt-3 text-sm text-zinc-600">
          <span v-for="(count, i) in sessionDistribution" :key="i" class="mr-4 inline-block">
            <span class="font-medium text-zinc-900">{{ i + 1 }} / 5:</span> {{ count }}
          </span>
        </p>
      </section>
    </template>
  </div>
</template>

<script setup lang="ts">
// Admin per-slot dashboard. Everything is fetched once and aggregated in the
// browser; the raw lists are filtered down to the selected slot before any
// per-TA or per-student work happens.
import { computed, defineAsyncComponent, onMounted, ref, watch } from 'vue'
import type { ChartData, ChartOptions } from 'chart.js'
import AppBadge from '../../components/common/AppBadge.vue'
import AppButton from '../../components/common/AppButton.vue'
import AppSelect from '../../components/common/AppSelect.vue'
import AppSpinner from '../../components/common/AppSpinner.vue'
import PersonStatsPanel from '../../components/charts/PersonStatsPanel.vue'
import {
  getEvaluations,
  getLabSessions,
  getQuestions,
  getSessionAssignments,
  getSubjects,
  getUsers,
} from '../../api/admin'
import type {
  EvaluationResponse,
  LabSession,
  QuestionResponse,
  SessionAssignment,
  SubjectResponse,
  UserResponse,
} from '../../types/api'
import { apiErrorMessage } from '../../utils/errors'
import { BASELINE, GRIDLINE, INK_MUTED, INK_SECONDARY, MARKING_RAMP } from '../../utils/charts'
import {
  MARKINGS,
  bumpDistribution,
  distributionMean,
  emptyDistribution,
  formatMean,
  percentage,
  type PersonStats,
} from '../../utils/stats'

// Chart.js is only needed here, so keep it out of the rest of the admin bundle.
const BaseChart = defineAsyncComponent(() => import('../../components/charts/BaseChart.vue'))

const loading = ref(true)
const refreshing = ref(false)
const loadError = ref('')
const lastUpdated = ref<Date | null>(null)

const subjects = ref<SubjectResponse[]>([])
const labSessions = ref<LabSession[]>([])
const users = ref<UserResponse[]>([])
const questions = ref<QuestionResponse[]>([])
const evaluations = ref<EvaluationResponse[]>([])
const assignments = ref<SessionAssignment[]>([])

const filterSubjectId = ref<number | null>(null)
const selectedSessionId = ref<number | null>(null)

/** One fetch of every list the page aggregates; used on mount and on refresh. */
async function loadAll(): Promise<void> {
  try {
    const [subjectList, sessionList, userList, questionList, evaluationList, assignmentList] =
      await Promise.all([
        getSubjects(),
        getLabSessions(),
        getUsers(),
        getQuestions(),
        getEvaluations(),
        getSessionAssignments(),
      ])
    subjects.value = subjectList
    labSessions.value = sessionList
    users.value = userList
    questions.value = questionList
    evaluations.value = evaluationList
    assignments.value = assignmentList
    lastUpdated.value = new Date()
    loadError.value = ''
    // Keep the current slot if it survived; otherwise default to the most
    // recent one so the page is useful on arrival.
    keepSelectionValid()
  } catch (error) {
    loadError.value = apiErrorMessage(error)
  }
}

onMounted(async () => {
  await loadAll()
  loading.value = false
})

async function refresh(): Promise<void> {
  refreshing.value = true
  try {
    await loadAll()
  } finally {
    refreshing.value = false
  }
}

const lastUpdatedLabel = computed(() => {
  const at = lastUpdated.value
  if (!at) return ''
  return at.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' })
})

function keepSelectionValid(): void {
  const stillVisible = selectableSessions.value.some((slot) => slot.id === selectedSessionId.value)
  if (!stillVisible) selectedSessionId.value = selectableSessions.value[0]?.id ?? null
}

// Keep the slot selection inside the filtered list.
watch(filterSubjectId, keepSelectionValid)

const usersById = computed(() => new Map(users.value.map((user) => [user.id, user])))
const subjectsById = computed(() => new Map(subjects.value.map((s) => [s.id, s])))

function sessionLabel(slot: LabSession): string {
  const subject = subjectsById.value.get(slot.subject_id)
  return `${subject ? subject.name : `Subject #${slot.subject_id}`} — ${slot.date}`
}

const selectableSessions = computed(() => {
  const list =
    filterSubjectId.value === null
      ? labSessions.value
      : labSessions.value.filter((slot) => slot.subject_id === filterSubjectId.value)
  return [...list].sort((a, b) => b.date.localeCompare(a.date))
})

const selectedSession = computed(
  () => labSessions.value.find((slot) => slot.id === selectedSessionId.value) ?? null,
)

// --- Slot-scoped slices. Everything downstream reads these, never the raw lists.

const sessionQuestions = computed(() => {
  const slot = selectedSession.value
  if (!slot) return []
  return questions.value.filter((q) => q.subject_id === slot.subject_id)
})

const sessionRoster = computed(() => {
  const slot = selectedSession.value
  if (!slot) return []
  return assignments.value.filter((a) => a.lab_session_id === slot.id)
})

const rosterStudents = computed(() => sessionRoster.value.filter((a) => a.role === 'student'))
const rosterTas = computed(() => sessionRoster.value.filter((a) => a.role === 'ta'))

const sessionEvaluations = computed(() => {
  const slot = selectedSession.value
  if (!slot) return []
  return evaluations.value.filter((e) => e.lab_session_id === slot.id)
})

const expectedTotal = computed(() => rosterStudents.value.length * sessionQuestions.value.length)

/**
 * The coverage numerator has to use the same population as the denominator.
 * Removing a student from the roster (or deleting a question) leaves their
 * evaluations behind, so counting every row here would report more work done
 * than was ever expected - three fully graded students, one removed, used to
 * read "150%". Those rows are still surfaced in the tables, badged
 * "Not on roster"; they just do not belong in the ratio.
 */
const countedEvaluations = computed(() => {
  const rosterIds = new Set(rosterStudents.value.map((a) => a.user_id))
  const questionIds = new Set(sessionQuestions.value.map((q) => q.id))
  return sessionEvaluations.value.filter(
    (e) => rosterIds.has(e.student_id) && questionIds.has(e.question_id),
  ).length
})

/** Null when nothing is expected, so the hero can say "—" instead of "0%". */
const coveragePercent = computed<number | null>(() => {
  if (expectedTotal.value === 0) return null
  if (countedEvaluations.value >= expectedTotal.value) return 100
  // Floor, never round: 249 of 250 is not "100%" on a page whose whole job is
  // to show that the last student has not been graded.
  return Math.min(99, Math.floor(percentage(countedEvaluations.value, expectedTotal.value)))
})

const coverageLabel = computed(() =>
  coveragePercent.value === null ? '—' : `${coveragePercent.value}%`,
)

const sessionDistribution = computed(() => {
  const dist = emptyDistribution()
  for (const evaluation of sessionEvaluations.value) {
    bumpDistribution(dist, evaluation.marking)
  }
  return dist
})

const sessionMean = computed(() => distributionMean(sessionDistribution.value))

// --- Per-person aggregation.

function blankStats(userId: number, onRoster: boolean): PersonStats {
  const user = usersById.value.get(userId)
  return {
    id: userId,
    name: user ? user.name : `User #${userId}`,
    email: user ? user.email : '',
    onRoster,
    total: 0,
    dist: emptyDistribution(),
    mean: null,
    studentsCovered: 0,
  }
}

/** Roster first (so zero-activity people are never dropped), evaluations joined on. */
const taStats = computed<PersonStats[]>(() => {
  const byId = new Map<number, PersonStats>()
  const seenStudents = new Map<number, Set<number>>()
  for (const assignment of rosterTas.value) {
    byId.set(assignment.user_id, blankStats(assignment.user_id, true))
    seenStudents.set(assignment.user_id, new Set())
  }
  for (const evaluation of sessionEvaluations.value) {
    let stats = byId.get(evaluation.ta_id)
    if (!stats) {
      stats = blankStats(evaluation.ta_id, false)
      byId.set(evaluation.ta_id, stats)
      seenStudents.set(evaluation.ta_id, new Set())
    }
    stats.total += 1
    bumpDistribution(stats.dist, evaluation.marking)
    seenStudents.get(evaluation.ta_id)?.add(evaluation.student_id)
  }
  return [...byId.values()]
    .map((stats) => ({
      ...stats,
      mean: distributionMean(stats.dist),
      studentsCovered: seenStudents.get(stats.id)?.size ?? 0,
    }))
    .sort((a, b) => b.total - a.total || a.name.localeCompare(b.name))
})

/**
 * The roster is the source of truth here: we enumerate every assigned student
 * and left-join their evaluations, so a student nobody graded still appears
 * with a total of 0 (and sorts to the top).
 */
const studentStats = computed<PersonStats[]>(() => {
  const byId = new Map<number, PersonStats>()
  for (const assignment of rosterStudents.value) {
    byId.set(assignment.user_id, blankStats(assignment.user_id, true))
  }
  for (const evaluation of sessionEvaluations.value) {
    let stats = byId.get(evaluation.student_id)
    if (!stats) {
      stats = blankStats(evaluation.student_id, false)
      byId.set(evaluation.student_id, stats)
    }
    stats.total += 1
    bumpDistribution(stats.dist, evaluation.marking)
  }
  return [...byId.values()]
    .map((stats) => ({ ...stats, mean: distributionMean(stats.dist) }))
    .sort((a, b) => a.total - b.total || a.name.localeCompare(b.name))
})

const pendingStudents = computed(() => studentStats.value.filter((s) => s.total === 0))
const offRosterStudents = computed(() => studentStats.value.filter((s) => !s.onRoster).length)
const offRosterTas = computed(() => taStats.value.filter((ta) => !ta.onRoster).length)

// --- The one chart this view still owns: the slot-wide marks histogram.

const sessionMarksData = computed<ChartData<'bar'>>(() => ({
  labels: MARKINGS.map((marking) => `${marking} / 5`),
  datasets: [
    {
      label: 'Evaluations',
      data: [...sessionDistribution.value],
      backgroundColor: [...MARKING_RAMP],
      maxBarThickness: 48,
      borderRadius: 4,
      borderSkipped: 'start',
    },
  ],
}))

const sessionMarksOptions = computed<ChartOptions<'bar'>>(() => ({
  responsive: true,
  maintainAspectRatio: false,
  animation: false,
  plugins: {
    legend: { display: false },
    tooltip: { displayColors: false },
  },
  scales: {
    x: {
      ticks: { color: INK_SECONDARY },
      grid: { display: false },
      border: { color: BASELINE },
    },
    y: {
      beginAtZero: true,
      ticks: { precision: 0, color: INK_MUTED },
      grid: { color: GRIDLINE },
      border: { color: BASELINE },
    },
  },
}))
</script>
